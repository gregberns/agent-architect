open Relude.Globals;

/**
 * Git repository information
 */
type repositoryInfo = {
  isRepository: bool,
  currentCommitSha: option(string),
  currentBranch: option(string),
  workingDirectory: string,
  hasUncommittedChanges: bool,
};

/**
 * Git command execution result
 */
[@deriving accessors]
type gitResult('a) =
  | Success('a)
  | Error(Js.Exn.t);

type param = {
  cwd: string,
  encoding: string,
};

/**
 * Node.js child_process bindings for executing git commands
 */
[@mel.module "child_process"]
external execSync: (string, param) => string = "execSync";

[@mel.module "child_process"]
external exec:
  (
    string,
    {. "cwd": string},
    (Js.nullable(Js.Exn.t), string, string) => unit
  ) =>
  unit =
  "exec";

/**
 * Execute a git command synchronously in the given directory
 */
let executeGitCommand =
    (command: string, workingDir: string): gitResult(string) =>
  try(
    execSync(
      command,
      {
        cwd: workingDir,
        encoding: "utf8",
      },
    )
    |> String.trim
    |> (trimmedOutput => Success(trimmedOutput))
  ) {
  | error =>
    Error(
      error
      |> Js.Exn.asJsExn
      |> Option.getOrElse("<<UNKNOWN EXN CONVERSION>>" |> RJs.Exn.make),
    )
  };

/**
 * Check if a directory is a git repository
 */
let isGitRepository = (path: string): bool => {
  switch (executeGitCommand("git rev-parse --git-dir", path)) {
  | Success(_) => true
  | Error(_) => false
  };
};

/**
 * Get the current commit SHA
 */
let getCurrentCommitSha = (repoPath: string): gitResult(string) =>
  executeGitCommand("git rev-parse HEAD", repoPath);

/**
 * Get the current branch name
 */
let getCurrentBranch = (repoPath: string): gitResult(string) =>
  executeGitCommand("git rev-parse --abbrev-ref HEAD", repoPath);

/**
 * Check if there are uncommitted changes in the working directory
 */
let hasUncommittedChanges = (repoPath: string): gitResult(bool) =>
  switch (executeGitCommand("git status --porcelain", repoPath)) {
  | Success(output) => Success(String.length(String.trim(output)) > 0)
  | Error(msg) => Error(msg)
  };

/**
 * Get the root directory of the git repository
 */
let getRepositoryRoot = (path: string): gitResult(string) =>
  switch (executeGitCommand("git rev-parse --show-toplevel", path)) {
  | Success(root) => Success(String.trim(root))
  | Error(msg) => Error(msg)
  };

/**
 * Get comprehensive repository information for a given path
 */
let getRepositoryInfo = (path: string): repositoryInfo => {
  let resultToOption = result =>
    switch (result) {
    | Success(value) => Some(value)
    | Error(_) => None
    };

  let resultToBool = (result, defaultValue) =>
    switch (result) {
    | Success(value) => value
    | Error(_) => defaultValue
    };

  isGitRepository(path)
    ? {
      isRepository: true,
      currentCommitSha: getCurrentCommitSha(path) |> resultToOption,
      currentBranch: getCurrentBranch(path) |> resultToOption,
      workingDirectory: path,
      hasUncommittedChanges:
        hasUncommittedChanges(path)
        |> (result => resultToBool(result, false)),
    }
    : {
      isRepository: false,
      currentCommitSha: None,
      currentBranch: None,
      workingDirectory: path,
      hasUncommittedChanges: false,
    };
};

/**
 * Get list of tracked files in the repository
 */
let getTrackedFiles = (repoPath: string): gitResult(list(string)) => {
  switch (executeGitCommand("git ls-files", repoPath)) {
  | Success(output) =>
    let files =
      output
      |> String.splitArray(~delimiter="\n")
      |> Array.toList
      |> List.filter(line => String.length(String.trim(line)) > 0);
    Success(files);
  | Error(msg) => Error(msg)
  };
};

/**
 * Get files that have been modified since the last commit
 */
let getModifiedFiles = (repoPath: string): gitResult(list(string)) => {
  switch (executeGitCommand("git diff --name-only HEAD", repoPath)) {
  | Success(output) =>
    let files =
      output
      |> String.splitArray(~delimiter="\n")
      |> Array.toList
      |> List.filter(line => String.length(String.trim(line)) > 0);
    Success(files);
  | Error(msg) => Error(msg)
  };
};

/**
 * Get untracked files in the repository
 */
let getUntrackedFiles = (repoPath: string): gitResult(list(string)) => {
  switch (
    executeGitCommand("git ls-files --others --exclude-standard", repoPath)
  ) {
  | Success(output) =>
    let files =
      output
      |> String.splitArray(~delimiter="\n")
      |> Array.toList
      |> List.filter(line => String.length(String.trim(line)) > 0);
    Success(files);
  | Error(msg) => Error(msg)
  };
};
