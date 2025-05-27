open Jest;
open Expect;
open TestUtils;
open Relude.Globals;
open Effects.AstParser;

module TestDependencies = {
  let getCurrentTimestamp = () => 123456.789;
  
  let parseTypeScript = (code, _config) => {
    /* Mock TypeScript parser responses */
    let mockResponse =
      switch (String.contains(~search="function", code)) {
      | true =>
        Js.Json.parseExn({js|{
          "type": "FunctionDeclaration",
          "name": {"text": "testFunction"},
          "start": 0,
          "end": 50
        }|js})
      | false when String.contains(~search="class", code) =>
        Js.Json.parseExn({js|{
          "type": "ClassDeclaration",
          "name": {"text": "TestClass"},
          "start": 0,
          "end": 60
        }|js})
      | false => Js.Json.parseExn({js|{}|js})
      };
    IO.pure(mockResponse);
  };

  let parseJavaScript = (code, _config) => {
    /* Mock Babel parser responses */
    let mockResponse =
      String.contains(~search="function", code)
        ? Js.Json.parseExn({js|{
            "type": "FunctionDeclaration",
            "id": {"name": "jsFunction"},
            "start": 0,
            "end": 45
          }|js})
        : Js.Json.parseExn({js|{}|js});
    IO.pure(mockResponse);
  };

  let convertToAstNode = (_jsonAst) => {
    /* Mock conversion to astNode */
    let mockNode = {
      nodeType: Function,
      name: Some("mockFunction"),
      location: Some({
        start: {line: 1, column: 0},
        end_: {line: 10, column: 20},
        source: None
      }),
      children: [],
      metadata: Js.Json.parseExn({js|{}|js})
    };
    IO.pure(mockNode);
  };
};

describe("AstParser", () => {
  let testDeps = {
    getCurrentTimestamp: TestDependencies.getCurrentTimestamp,
    parseTypeScript: TestDependencies.parseTypeScript,
    parseJavaScript: TestDependencies.parseJavaScript,
    convertToAstNode: TestDependencies.convertToAstNode,
  };

  describe("parseSourceCode", () => {
    Test.testIO("should parse TypeScript function successfully", () => {
      let code = "function testFunction() { return true; }";
      let fileName = "test.ts";

      parseSourceCode(code, fileName, ~deps=testDeps, ())
      |> IO.map(parseResult => 
           expect(parseResult.parserUsed) |> toEqual("typescript")
         );
    });

    Test.testIO("should parse JavaScript with Babel successfully", () => {
      let code = "function jsFunction() { return 42; }";
      let fileName = "test.js";

      parseSourceCode(code, fileName, ~deps=testDeps, ())
      |> IO.map(parseResult => 
           expect(parseResult.parserUsed) |> toEqual("javascript")
         );
    });

    Test.testIO("should handle empty code", () => {
      let code = "";
      let fileName = "empty.ts";

      parseSourceCode(code, fileName, ~deps=testDeps, ())
      |> IO.map(parseResult => 
           expect(parseResult.ast.nodeType) |> toEqual(Function)
         );
    });
  });


  describe("extractNodesByType", () => {
    test("should filter nodes by type", () => {
      let rootNode = {
        nodeType: Function,
        name: Some("root"),
        location: None,
        children: [
          {
            nodeType: Function,
            name: Some("func1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
          {
            nodeType: Class,
            name: Some("Class1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
        ],
        metadata: Js.Json.parseExn({js|{}|js}),
      };

      let functions = extractNodesByType(rootNode, Function);
      expect(List.length(functions)) |> toBe(2);
    })
  });

  describe("getFunctions", () => {
    test("should extract function nodes", () => {
      let rootNode = {
        nodeType: Function,
        name: Some("root"),
        location: None,
        children: [
          {
            nodeType: Function,
            name: Some("func1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
          {
            nodeType: Class,
            name: Some("Class1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
        ],
        metadata: Js.Json.parseExn({js|{}|js}),
      };

      let functionNodes = getFunctions(rootNode);
      expect(List.length(functionNodes)) |> toBe(2);
    })
  });

  describe("getClasses", () => {
    test("should extract class nodes", () => {
      let rootNode = {
        nodeType: Class,
        name: Some("root"),
        location: None,
        children: [
          {
            nodeType: Function,
            name: Some("func1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
          {
            nodeType: Class,
            name: Some("Class1"),
            location: None,
            children: [],
            metadata: Js.Json.parseExn({js|{}|js}),
          },
        ],
        metadata: Js.Json.parseExn({js|{}|js}),
      };

      let classNodes = getClasses(rootNode);
      expect(List.length(classNodes)) |> toBe(2);
    })
  });

  describe("getImports", () => {
    test("should extract import nodes", () => {
      let rootNode = {
        nodeType: Import,
        name: Some("./module"),
        location: None,
        children: [],
        metadata: Js.Json.parseExn({js|{}|js}),
      };

      let importNodes = getImports(rootNode);
      expect(List.length(importNodes)) |> toBe(1);
    })
  });

  describe("getExports", () => {
    test("should extract export nodes", () => {
      let rootNode = {
        nodeType: Export,
        name: Some("myExport"),
        location: None,
        children: [],
        metadata: Js.Json.parseExn({js|{}|js}),
      };

      let exportNodes = getExports(rootNode);
      expect(List.length(exportNodes)) |> toBe(1);
    })
  });

  describe("defaultTypescriptConfig", () => {
    test("should have correct default values", () => {
      expect(defaultTypescriptConfig.includeComments) |> toBe(true);
    })
  });

  describe("defaultJavascriptConfig", () => {
    test("should have correct default values", () => {
      expect(defaultJavascriptConfig.includeComments) |> toBe(true);
    })
  });

});
