open Relude.Globals;
open Bindings.NodeJs;

/**
 * File information record containing metadata about discovered files
 */
type fileInfo = {
  path: string,
  name: string,
  extension: option(string),
  size: option(int),
  isDirectory: bool,
};

/**
 * Configuration for file discovery operations
 */
type discoveryConfig = {
  targetExtensions: list(string),
  followSymlinks: bool,
  maxDepth: option(int),
  gitignorePatterns: list(string),
};

/**
 * Default configuration for JavaScript/TypeScript projects
 */
let defaultJsConfig: discoveryConfig = {
  targetExtensions: [".js", ".jsx", ".ts", ".tsx", ".json"],
  followSymlinks: false,
  maxDepth: None,
  gitignorePatterns: [],
};

/**
 * Parse a .gitignore file and return a list of patterns
 */
let parseGitignore = (gitignorePath: string): IO.t(list(string), Js.Exn.t) => {
  Fs.readFileSync(gitignorePath, `utf8)
  |> IO.map(content =>
       content
       |> String.splitArray(~delimiter="\n")
       |> Array.toList
       |> List.map(String.trim)
       |> List.filter(line =>
            String.length(line) > 0 && !String.startsWith(~search="#", line)
          )
     )
  |> IO.catchError(_ => IO.pure([]));
};

/**
 * Check if a path matches any gitignore pattern
 * Simple glob-like matching for common patterns
 */
let matchesGitignorePattern = (path: string, pattern: string): bool => {
  let normalizedPath =
    if (String.startsWith(~search="./", path)) {
      String.sliceToEnd(2, path);
    } else {
      path;
    };

  // Handle exact matches
  if (String.eq(pattern, normalizedPath)) {
    true;
  } else if
    // Handle directory patterns (ending with /)
    (String.endsWith(~search="/", pattern)) {
    let dirPattern = String.slice(0, String.length(pattern) - 1, pattern);
    String.startsWith(~search=dirPattern ++ "/", normalizedPath)
    || String.eq(dirPattern, normalizedPath);
  } else if
    // Handle wildcard patterns (basic support)
    (String.contains(~search="*", pattern)) {
    // For now, handle simple cases like "*.ext" and "dir/*"
    if (String.startsWith(~search="*.", pattern)) {
      let ext = String.sliceToEnd(1, pattern);
      String.endsWith(~search=ext, normalizedPath);
    } else if (String.endsWith(~search="/*", pattern)) {
      let dir = String.slice(0, String.length(pattern) - 2, pattern);
      String.startsWith(~search=dir ++ "/", normalizedPath);
    } else {
      false; // More complex patterns not implemented yet
    };
  } else {
    // Handle file/directory name matches anywhere in path
    String.contains(~search=pattern, normalizedPath)
    || String.contains(
         ~search="/" ++ pattern ++ "/",
         "/" ++ normalizedPath ++ "/",
       );
  };
};

/**
 * Check if a path should be ignored based on gitignore patterns
 */
let shouldIgnoreFile = (path: string, patterns: list(string)): bool =>
  patterns
  |> List.filter(matchesGitignorePattern(path, _))
  |> List.isNotEmpty;

/**
 * Get file extension from a filename
 */
let getFileExtension = (filename: string): option(string) => {
  switch (String.lastIndexOf(~search=".", filename)) {
  | Some(lastDotIndex) when lastDotIndex < String.length(filename) - 1 =>
    Some(String.sliceToEnd(lastDotIndex, filename))
  | _ => None
  };
};

/**
 * Check if file extension matches target extensions
 */
let hasTargetExtension =
    (filename: string, targetExtensions: list(string)): bool => {
  switch (getFileExtension(filename)) {
  | None => false
  | Some(ext) => List.String.contains(ext, targetExtensions)
  };
};

/**
 * Read directory contents and return file information
 */

/**
 * Convert Node.js stats to our fileInfo type
 */
let statsToFileInfo = (path: string, stats: nodeStats): fileInfo => {
  let filename =
    path
    |> String.splitArray(~delimiter="/")
    |> Array.last
    |> Option.getOrElse("");

  {
    path,
    name: filename,
    extension: getFileExtension(filename),
    size: Some(stats.size),
    isDirectory: stats.isDirectory(),
  };
};

/**
 * Recursively discover files in a directory
 */
let rec discoverFiles =
        (~currentDepth: int=0, ~config: discoveryConfig, rootPath: string)
        : IO.t(list(fileInfo), Js.Exn.t) =>
  // Check depth limit
  switch (config.maxDepth) {
  | Some(maxDepth) when currentDepth >= maxDepth => IO.pure([])
  | _ =>
    Bindings.NodeJs.Fs.readdirSync(rootPath)
    |> IO.flatMap(entries =>
         entries
         |> Array.toList
         |> List.map(entry => Path.join(rootPath, entry))
         |> List.filter(path =>
              !shouldIgnoreFile(path, config.gitignorePatterns)
            )
         |> List.IO.traverse(path =>
              Bindings.NodeJs.Fs.statSync(path)
              |> IO.flatMap(stats => {
                   let fileInfo = statsToFileInfo(path, stats);

                   if (fileInfo.isDirectory) {
                     // Recursively process subdirectory
                     discoverFiles(
                       ~currentDepth=currentDepth + 1,
                       ~config,
                       path,
                     );
                   } else if (hasTargetExtension(
                                fileInfo.name,
                                config.targetExtensions,
                              )) {
                     IO.pure([fileInfo]);
                   } else {
                     IO.pure([]);
                   };
                 })
              |> IO.catchError(_ => IO.pure([]))
            )  // Skip files that can't be accessed
         |> IO.map(List.flatten)
       )
    |> IO.catchError(_ => IO.pure([])) // Return empty list if directory can't be read
  };

/**
 * Discover files in a project directory with gitignore support
 */
let discoverProjectFiles =
    (projectRoot: string, ~customConfig: option(discoveryConfig)=?, ())
    : IO.t(list(fileInfo), Js.Exn.t) => {
  Path.join(projectRoot, ".gitignore")
  |> parseGitignore
  |> IO.flatMap(gitignorePatterns => {
       let config =
         customConfig
         |> Option.fold(
              {
                ...defaultJsConfig,
                gitignorePatterns,
              },
              custom =>
              {
                ...custom,
                gitignorePatterns:
                  custom.gitignorePatterns @ gitignorePatterns,
              }
            );
       discoverFiles(~config, projectRoot);
     });
};

/**
 * Get project files filtered by extension
 */
let getProjectFilesByExtension =
    (projectRoot: string, extensions: list(string))
    : IO.t(list(fileInfo), Js.Exn.t) => {
  discoverProjectFiles(
    projectRoot,
    ~customConfig={
      ...defaultJsConfig,
      targetExtensions: extensions,
    },
    (),
  );
};
