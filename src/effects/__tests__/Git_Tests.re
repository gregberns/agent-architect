open Jest;
open Expect;
open Effects.Git;

describe("Git", () => {
  describe("gitResult", () => {
    test("should handle Success case correctly", () => {
      let result: gitResult(string) = Success("test");
      switch (result) {
      | Success(value) => expect(value) |> toEqual("test")
      | Error(_) => expect(false) |> toEqual(true)
      };
    });

    test("should handle Error case correctly", () => {
      let result: gitResult(string) = Error("test error" |> RJs.Exn.make);

      switch (result) {
      | Error(msg) =>
        expect(msg |> Js.Exn.message) |> toEqual(Some("test error"))
      | Success(_) => expect(false) |> toEqual(true)
      };
    });
  });
  describe("executeGitCommand", () => {
    test("should handle git command errors gracefully", () => {
      // Test with a non-existent directory
      let result = executeGitCommand("git status", "/non/existent/path");
      switch (result) {
      | Error(_) => expect(true) |> toEqual(true)
      | Success(_) => expect(false) |> toEqual(true) // Should not succeed
      };
    })
  });
  describe("isGitRepository", () => {
    test("should detect git repository correctly", () => {
      // Test current directory (should be a git repo)
      let currentDir = ".";
      expect(isGitRepository(currentDir)) |> toEqual(true);
    });
    test("should return false for non-git directory", () => {
      // Test a non-git directory (if it exists)
      expect(isGitRepository("/tmp"))
      |> toEqual(false)
    });
  });
  describe("getCurrentCommitSha", () => {
    test("should return commit SHA with valid length", () => {
      let result = getCurrentCommitSha(".");
      switch (result) {
      | Success(sha) => expect(String.length(sha) >= 7) |> toEqual(true)
      | Error(_) => expect(false) |> toEqual(true)
      };
    });
    test("should return commit SHA with valid hexadecimal format", () => {
      let result = getCurrentCommitSha(".");
      switch (result) {
      | Success(sha) =>
        expect(Js.Re.test(~str=sha, [%re "/^[a-f0-9]+$/i"]))
        |> toEqual(true)
      | Error(_) => expect(false) |> toEqual(true)
      };
    });
    test("should return error for non-git directory", () => {
      let result = getCurrentCommitSha("/tmp");
      switch (result) {
      | Error(_) => expect(true) |> toEqual(true)
      | Success(_) => expect(false) |> toEqual(true)
      };
    });
  });
  describe("getCurrentBranch", () => {
    test("should return branch name for valid git repo", () => {
      let result = getCurrentBranch(".");
      switch (result) {
      | Success(branch) =>
        // Branch name should not be empty
        expect(String.length(branch) > 0) |> toEqual(true)
      | Error(_) => expect(false) |> toEqual(true) // Should succeed in a git repo
      };
    })
  });
  describe("getRepositoryInfo", () => {
    test("should detect repository correctly", () => {
      let info = getRepositoryInfo(".");
      expect(info.isRepository) |> toEqual(true);
    });
    test("should return correct working directory", () => {
      let info = getRepositoryInfo(".");
      expect(info.workingDirectory) |> toEqual(".");
    });
    test("should have valid commit SHA", () => {
      let info = getRepositoryInfo(".");
      switch (info.currentCommitSha) {
      | Some(sha) => expect(String.length(sha) >= 7) |> toEqual(true)
      | None => expect(false) |> toEqual(true)
      };
    });
    test("should have valid branch name", () => {
      let info = getRepositoryInfo(".");
      switch (info.currentBranch) {
      | Some(branch) => expect(String.length(branch) > 0) |> toEqual(true)
      | None => expect(false) |> toEqual(true)
      };
    });
    test("should return false for non-repository", () => {
      let info = getRepositoryInfo("/tmp");
      expect(info.isRepository) |> toEqual(false);
    });
    test("should return None commit SHA for non-repository", () => {
      let info = getRepositoryInfo("/tmp");
      expect(info.currentCommitSha) |> toEqual(None);
    });
    test("should return None branch for non-repository", () => {
      let info = getRepositoryInfo("/tmp");
      expect(info.currentBranch) |> toEqual(None);
    });
    test("should return false for uncommitted changes in non-repository", () => {
      let info = getRepositoryInfo("/tmp");
      expect(info.hasUncommittedChanges) |> toEqual(false);
    });
  });
  describe("getTrackedFiles", () => {
    test("should return non-negative list length", () => {
      let result = getTrackedFiles(".");
      switch (result) {
      | Success(files) => expect(List.length(files) >= 0) |> toEqual(true)
      | Error(_) => expect(false) |> toEqual(true)
      };
    });
    test("should include package.json in tracked files", () => {
      let result = getTrackedFiles(".");
      switch (result) {
      | Success(files) =>
        let hasPackageJson =
          List.filter(
            file => String.endsWith(~search="package.json", file),
            files,
          )
          |> List.isNotEmpty;
        expect(hasPackageJson) |> toEqual(true);
      | Error(_) => expect(false) |> toEqual(true)
      };
    });
  });
  describe("hasUncommittedChanges", () => {
    test("should determine if there are uncommitted changes", () => {
      let result = hasUncommittedChanges(".");
      switch (result) {
      | Success(hasChanges) =>
        // Should return a boolean (either true or false is valid)
        expect(hasChanges == true || hasChanges == false) |> toEqual(true)
      | Error(_) => expect(false) |> toEqual(true)
      };
    })
  });
});
