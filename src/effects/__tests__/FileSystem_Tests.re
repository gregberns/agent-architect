open Jest;
open Expect;
open TestUtils;
open Effects.FileSystem;
describe("FileSystem", () => {
  describe("parseGitignore", () => {
    Test.testIO("should return empty list for non-existent file", () =>
      parseGitignore("non-existent-file")
      |> IO.map(patterns => expect(patterns) |> toEqual([]))
    )
  });
  describe("getFileExtension", () => {
    test("should extract .js extension", () =>
      expect(getFileExtension("test.js")) |> toEqual(Some(".js"))
    );
    test("should extract extension from nested filename", () =>
      expect(getFileExtension("test.min.js")) |> toEqual(Some(".js"))
    );
    test("should return None for no extension", () =>
      expect(getFileExtension("test")) |> toEqual(None)
    );
    test("should handle dotfiles", () =>
      expect(getFileExtension(".gitignore")) |> toEqual(Some(".gitignore"))
    );
    test("should handle empty filename", () =>
      expect(getFileExtension("")) |> toEqual(None)
    );
  });
  describe("hasTargetExtension", () => {
    let jsExtensions = [".js", ".jsx", ".ts", ".tsx"];
    test("should match .js extension", () =>
      expect(hasTargetExtension("test.js", jsExtensions)) |> toEqual(true)
    );
    test("should match .tsx extension", () =>
      expect(hasTargetExtension("component.tsx", jsExtensions))
      |> toEqual(true)
    );
    test("should not match .py extension", () =>
      expect(hasTargetExtension("test.py", jsExtensions)) |> toEqual(false)
    );
    test("should not match file without extension", () =>
      expect(hasTargetExtension("README", jsExtensions)) |> toEqual(false)
    );
  });
  describe("matchesGitignorePattern", () => {
    test("should match exact directory name", () =>
      expect(matchesGitignorePattern("node_modules", "node_modules"))
      |> toEqual(true)
    );
    test("should match filename in subdirectory", () =>
      expect(matchesGitignorePattern("src/test.js", "test.js"))
      |> toEqual(true)
    );
    test("should not match different filename", () =>
      expect(matchesGitignorePattern("test.js", "other.js"))
      |> toEqual(false)
    );
    test("should match directory patterns", () => {
      expect(matchesGitignorePattern("node_modules", "node_modules/"))
      |> toEqual(true)
      |> ignore;
      expect(
        matchesGitignorePattern("node_modules/package", "node_modules/"),
      )
      |> toEqual(true)
      |> ignore;
      expect(
        matchesGitignorePattern("src/node_modules/test", "node_modules/"),
      )
      |> toEqual(false);
    });
    test("should match wildcard patterns", () => {
      expect(matchesGitignorePattern("test.log", "*.log"))
      |> toEqual(true)
      |> ignore;
      expect(matchesGitignorePattern("debug.log", "*.log"))
      |> toEqual(true)
      |> ignore;
      expect(matchesGitignorePattern("test.js", "*.log"))
      |> toEqual(false)
      |> ignore;
      expect(matchesGitignorePattern("dist/bundle.js", "dist/*"))
      |> toEqual(true)
      |> ignore;
      expect(matchesGitignorePattern("dist/css/style.css", "dist/*"))
      |> toEqual(true)
      |> ignore;
      expect(matchesGitignorePattern("src/index.js", "dist/*"))
      |> toEqual(false);
    });
    test("should handle normalized paths", () => {
      expect(matchesGitignorePattern("./node_modules", "node_modules"))
      |> toEqual(true)
      |> ignore;
      expect(matchesGitignorePattern("./src/test.js", "test.js"))
      |> toEqual(true);
    });
  });
  describe("shouldIgnoreFile", () => {
    let patterns = ["node_modules", "*.log", "dist/", ".DS_Store"];
    test("should ignore node_modules", () =>
      expect(shouldIgnoreFile("node_modules", patterns)) |> toEqual(true)
    );
    test("should ignore .log files", () =>
      expect(shouldIgnoreFile("debug.log", patterns)) |> toEqual(true)
    );
    test("should ignore dist/ files", () =>
      expect(shouldIgnoreFile("dist/bundle.js", patterns)) |> toEqual(true)
    );
    test("should ignore .DS_Store", () =>
      expect(shouldIgnoreFile(".DS_Store", patterns)) |> toEqual(true)
    );
    test("should not ignore src files", () =>
      expect(shouldIgnoreFile("src/index.js", patterns)) |> toEqual(false)
    );
    test("should not ignore package.json", () =>
      expect(shouldIgnoreFile("package.json", patterns)) |> toEqual(false)
    );
    test("should not ignore README.md", () =>
      expect(shouldIgnoreFile("README.md", patterns)) |> toEqual(false)
    );
  });
  describe("discoveryConfig", () => {
    test("should have correct target extensions", () =>
      expect(defaultJsConfig.targetExtensions)
      |> toEqual([".js", ".jsx", ".ts", ".tsx", ".json"])
    );
    test("should not follow symlinks by default", () =>
      expect(defaultJsConfig.followSymlinks) |> toEqual(false)
    );
    test("should have no max depth by default", () =>
      expect(defaultJsConfig.maxDepth) |> toEqual(None)
    );
  });
});
