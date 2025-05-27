open Jest;
open Expect;
open Relude.Globals;
open Effects.CodebaseDiscovery;

describe("CodebaseDiscovery", () => {
  test("should filter test files correctly when includeTestFiles is false", () => {
    let testFiles = [
      {
        Effects.FileSystem.path: "src/Component.js",
        name: "Component.js",
        extension: Some(".js"),
        size: Some(100),
        isDirectory: false,
      },
      {
        Effects.FileSystem.path: "src/Component.test.js",
        name: "Component.test.js",
        extension: Some(".js"),
        size: Some(50),
        isDirectory: false,
      },
      {
        Effects.FileSystem.path: "src/__tests__/Helper.js",
        name: "Helper.js",
        extension: Some(".js"),
        size: Some(75),
        isDirectory: false,
      },
    ];

    let config = {
      ...defaultJsProjectConfig,
      includeTestFiles: false,
    };
    let filtered = filterFiles(testFiles, config);

    expect(List.length(filtered)) |> toEqual(1);
  });

  test("should include test files when includeTestFiles is true", () => {
    let testFiles = [
      {
        Effects.FileSystem.path: "src/Component.js",
        name: "Component.js",
        extension: Some(".js"),
        size: Some(100),
        isDirectory: false,
      },
      {
        Effects.FileSystem.path: "src/Component.test.js",
        name: "Component.test.js",
        extension: Some(".js"),
        size: Some(50),
        isDirectory: false,
      },
    ];

    let config = {
      ...defaultJsProjectConfig,
      includeTestFiles: true,
    };
    let filtered = filterFiles(testFiles, config);

    expect(List.length(filtered)) |> toEqual(2);
  });

  test("should exclude files based on patterns", () => {
    let testFiles = [
      {
        Effects.FileSystem.path: "src/Component.js",
        name: "Component.js",
        extension: Some(".js"),
        size: Some(100),
        isDirectory: false,
      },
      {
        Effects.FileSystem.path: "node_modules/package/index.js",
        name: "index.js",
        extension: Some(".js"),
        size: Some(50),
        isDirectory: false,
      },
      {
        Effects.FileSystem.path: "dist/bundle.js",
        name: "bundle.js",
        extension: Some(".js"),
        size: Some(200),
        isDirectory: false,
      },
    ];

    let filtered = filterFiles(testFiles, defaultJsProjectConfig);

    expect(List.length(filtered)) |> toEqual(1);
  });
});
