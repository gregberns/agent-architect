open Relude.Globals;

/**
 * Codebase Discovery Module
 *
 * Provides functionality to scan project directories and discover source files
 * with Git integration for version tracking.
 */

/**
 * Configuration for JavaScript/TypeScript project discovery
 */
type jsProjectConfig = {
  targetExtensions: list(string),
  excludePatterns: list(string),
  includeTestFiles: bool,
  maxDepth: option(int),
};

/**
 * Project metadata containing discovery results
 */
type projectMetadata = {
  rootPath: string,
  commitSha: option(string),
  isGitRepository: bool,
  discoveredFiles: list(FileSystem.fileInfo),
  totalFiles: int,
  discoveryTimestamp: float,
};

/**
 * Default configuration for JavaScript/TypeScript projects
 */
let defaultJsProjectConfig: jsProjectConfig = {
  targetExtensions: [".js", ".jsx", ".ts", ".tsx", ".json"],
  excludePatterns: ["node_modules", "dist", "build", ".git"],
  includeTestFiles: false,
  maxDepth: None,
};

/**
 * Configuration that includes test files
 */
let jsProjectConfigWithTests: jsProjectConfig = {
  ...defaultJsProjectConfig,
  includeTestFiles: true,
  excludePatterns: ["node_modules", "dist", "build", ".git"],
};

/**
 * Check if a file path should be excluded based on patterns
 */
let shouldExcludeFile =
    (filePath: string, excludePatterns: list(string)): bool => {
  excludePatterns
  |> List.filter(pattern => String.contains(~search=pattern, filePath))
  |> List.isNotEmpty;
};

/**
 * Check if a file is a test file based on common patterns
 */
let isTestFile = (filePath: string): bool => {
  let testPatterns = [".test.", ".spec.", "__tests__", "__test__"];
  testPatterns
  |> List.filter(pattern => String.contains(~search=pattern, filePath))
  |> List.isNotEmpty;
};

/**
 * Filter files based on project configuration
 */
let filterFiles =
    (files: list(FileSystem.fileInfo), config: jsProjectConfig)
    : list(FileSystem.fileInfo) => {
  files
  |> List.filter(({path, _}: FileSystem.fileInfo) => {
       // Check if file should be excluded by patterns
       let isExcluded = shouldExcludeFile(path, config.excludePatterns);

       // Check if it's a test file and we should include/exclude tests
       let isTest = isTestFile(path);
       let includeFile =
         if (isTest) {
           config.includeTestFiles;
         } else {
           true;
         };

       !isExcluded && includeFile;
     });
};

/**
 * Dependencies for file system operations and time
 */
type dependencies = {
  getCurrentTimestamp: unit => float,
  discoverFiles:
    (string, ~customConfig: option(FileSystem.discoveryConfig), unit) =>
    IO.t(list(FileSystem.fileInfo), Js.Exn.t),
  getGitInfo: string => IO.t((bool, option(string)), Js.Exn.t),
};

/**
 * Get Git repository information for a project
 */
let getGitInfo =
    (projectRoot: string): IO.t((bool, option(string)), Js.Exn.t) => {
  let isRepo = Git.isGitRepository(projectRoot);

  if (isRepo) {
    switch (Git.getCurrentCommitSha(projectRoot)) {
    | Git.Success(sha) => IO.pure((true, Some(sha)))
    | Git.Error(_) => IO.pure((true, None))
    };
  } else {
    IO.pure((false, None));
  };
};

/**
 * Default dependencies using real implementations
 */
let defaultDependencies: dependencies = {
  getCurrentTimestamp: () => Js.Date.now(),
  discoverFiles: (path, ~customConfig, ()) =>
    FileSystem.discoverProjectFiles(path, ~customConfig?, ()),
  getGitInfo,
};

/**
 * Discover all relevant files in a project directory
 */
let discoverProjectFiles =
    (
      projectRoot: string,
      ~config: jsProjectConfig=defaultJsProjectConfig,
      ~deps: dependencies=defaultDependencies,
      (),
    )
    : IO.t(list(FileSystem.fileInfo), Js.Exn.t) => {
  let discoveryConfig: FileSystem.discoveryConfig = {
    targetExtensions: config.targetExtensions,
    followSymlinks: false,
    maxDepth: config.maxDepth,
    gitignorePatterns: [] // Will be loaded from .gitignore
  };

  deps.discoverFiles(projectRoot, ~customConfig=Some(discoveryConfig), ())
  |> IO.map(files => filterFiles(files, config));
};

module IOWithError =
  IO.WithError({
    type t = Js.Exn.t;
  });

/**
 * Perform complete project discovery with Git integration
 */
let discoverProject =
    (
      projectRoot: string,
      ~config: jsProjectConfig=defaultJsProjectConfig,
      ~deps: dependencies=defaultDependencies,
      (),
    )
    : IO.t(projectMetadata, Js.Exn.t) => {
  let timestamp = deps.getCurrentTimestamp();

  // Run file discovery and git info in parallel
  IOWithError.mapTuple2(
    (files, (isGitRepo, commitSha)) => {
      {
        rootPath: projectRoot,
        commitSha,
        isGitRepository: isGitRepo,
        discoveredFiles: files,
        totalFiles: List.length(files),
        discoveryTimestamp: timestamp,
      }
    },
    (
      discoverProjectFiles(projectRoot, ~config, ~deps, ()),
      deps.getGitInfo(projectRoot),
    ),
  );
};

/**
 * Get a summary of discovered project metadata
 */
let getProjectSummary = (metadata: projectMetadata): string => {
  let gitInfo =
    if (metadata.isGitRepository) {
      switch (metadata.commitSha) {
      | Some(sha) => "Git repository (SHA: " ++ sha ++ ")"
      | None => "Git repository (SHA unavailable)"
      };
    } else {
      "Not a Git repository";
    };

  let fileCount = Int.toString(metadata.totalFiles);

  "Project: "
  ++ metadata.rootPath
  ++ "\\n"
  ++ "Files discovered: "
  ++ fileCount
  ++ "\\n"
  ++ "Status: "
  ++ gitInfo
  ++ "\\n"
  ++ "Discovery completed at: "
  ++ Float.toString(metadata.discoveryTimestamp);
};
