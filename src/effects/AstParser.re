open Relude.Globals;

/**
 * AST Parser Module
 *
 * Provides TypeScript and JavaScript AST parsing capabilities using:
 * - TypeScript Compiler API for .ts/.tsx files
 * - @babel/parser for .js/.jsx files
 *
 * Supports code analysis for imports, exports, functions, classes, and variables.
 */

/**
 * Represents different types of code constructs we can parse
 */
type nodeType =
  | Function
  | Class
  | Variable
  | Import
  | Export
  | Interface
  | Type
  | Enum
  | Unknown;

/**
 * Position information for nodes in source code
 */
type position = {
  line: int,
  column: int,
};

/**
 * Source location with start and end positions
 */
type sourceLocation = {
  start: position,
  end_: position,
  source: option(string),
};

/**
 * Parsed AST node with metadata
 */
type astNode = {
  nodeType,
  name: option(string),
  location: option(sourceLocation),
  children: list(astNode),
  metadata: Js.Json.t,
};

/**
 * Parser configuration options
 */
type parserConfig = {
  includeComments: bool,
  includeTokens: bool,
  preserveParens: bool,
  allowImportExportEverywhere: bool,
  allowReturnOutsideFunction: bool,
  plugins: list(string),
};

/**
 * Parser result containing AST and metadata
 */
type parseResult = {
  ast: astNode,
  sourceText: string,
  fileName: string,
  parseTime: float,
  parserUsed: string,
};

/**
 * Default parser configuration for TypeScript
 */
let defaultTypescriptConfig: parserConfig = {
  includeComments: true,
  includeTokens: false,
  preserveParens: false,
  allowImportExportEverywhere: true,
  allowReturnOutsideFunction: false,
  plugins: ["typescript", "jsx"],
};

/**
 * Default parser configuration for JavaScript
 */
let defaultJavascriptConfig: parserConfig = {
  includeComments: true,
  includeTokens: false,
  preserveParens: false,
  allowImportExportEverywhere: true,
  allowReturnOutsideFunction: false,
  plugins: [
    "jsx",
    "asyncGenerators",
    "bigInt",
    "classProperties",
    "decorators-legacy",
    "doExpressions",
    "dynamicImport",
    "exportDefaultFrom",
    "exportNamespaceFrom",
    "functionSent",
    "functionBind",
    "importMeta",
    "nullishCoalescingOperator",
    "numericSeparator",
    "objectRestSpread",
    "optionalCatchBinding",
    "optionalChaining",
    "throwExpressions",
    "topLevelAwait",
    "trailingFunctionCommas",
  ],
};
/**
 * Dependencies for parser operations (for testability)
 */
type parserDependencies = {
  getCurrentTimestamp: unit => float,
  parseTypeScript: (string, parserConfig) => IO.t(Js.Json.t, Js.Exn.t),
  parseJavaScript: (string, parserConfig) => IO.t(Js.Json.t, Js.Exn.t),
  convertToAstNode: Js.Json.t => IO.t(astNode, Js.Exn.t),
};

/**
 * Convert TypeScript AST node type to our nodeType
 */
let convertNodeType = (tsNodeType: string): nodeType => {
  switch (tsNodeType) {
  | "FunctionDeclaration"
  | "ArrowFunction"
  | "FunctionExpression"
  | "MethodDefinition" => Function
  | "ClassDeclaration"
  | "ClassExpression" => Class
  | "VariableDeclaration"
  | "VariableDeclarator" => Variable
  | "ImportDeclaration" => Import
  | "ExportNamedDeclaration"
  | "ExportDefaultDeclaration"
  | "ExportAllDeclaration" => Export
  | "InterfaceDeclaration" => Interface
  | "TypeAliasDeclaration" => Type
  | "EnumDeclaration" => Enum
  | _ => Unknown
  };
};

/**
 * Extract name from AST node JSON
 */
let extractNodeName = (nodeJson: Js.Json.t): option(string) => {
  nodeJson
  |> Js.Json.decodeObject
  |> Option.flatMap(obj => {
       // Try different possible name fields
       let nameFields = ["name", "id", "key", "local"];
       nameFields
       |> List.mapOption(field => {
            Js.Dict.get(obj, field)
            |> Option.flatMap(value =>
                 value
                 |> Js.Json.decodeObject
                 |> Option.flatMap(nameObj =>
                      Js.Dict.get(nameObj, "name")
                      |> Option.flatMap(Js.Json.decodeString)
                    )
                 |> Option.alt(_, Js.Json.decodeString(value))
               )
          })
       |> List.head;
     });
};

/**
 * Extract source location from AST node JSON
 */
let extractSourceLocation = (nodeJson: Js.Json.t): option(sourceLocation) => {
  nodeJson
  |> Js.Json.decodeObject
  |> Option.flatMap(obj => {
       let loc = Js.Dict.get(obj, "loc");
       switch (loc) {
       | None => None
       | Some(locJson) =>
         locJson
         |> Js.Json.decodeObject
         |> Option.flatMap(locObj => {
              let start = Js.Dict.get(locObj, "start");
              let end_ = Js.Dict.get(locObj, "end");
              switch (start, end_) {
              | (Some(startJson), Some(endJson)) =>
                let startPos =
                  startJson
                  |> Js.Json.decodeObject
                  |> Option.flatMap(startObj => {
                       let line =
                         Js.Dict.get(startObj, "line")
                         |> Option.flatMap(Js.Json.decodeNumber)
                         |> Option.map(Float.toInt);
                       let column =
                         Js.Dict.get(startObj, "column")
                         |> Option.flatMap(Js.Json.decodeNumber)
                         |> Option.map(Float.toInt);
                       switch (line, column) {
                       | (Some(l), Some(c)) =>
                         Some({
                           line: l,
                           column: c,
                         })
                       | _ => None
                       };
                     });
                let endPos =
                  endJson
                  |> Js.Json.decodeObject
                  |> Option.flatMap(endObj => {
                       let line =
                         Js.Dict.get(endObj, "line")
                         |> Option.flatMap(Js.Json.decodeNumber)
                         |> Option.map(Float.toInt);
                       let column =
                         Js.Dict.get(endObj, "column")
                         |> Option.flatMap(Js.Json.decodeNumber)
                         |> Option.map(Float.toInt);
                       switch (line, column) {
                       | (Some(l), Some(c)) =>
                         Some({
                           line: l,
                           column: c,
                         })
                       | _ => None
                       };
                     });
                switch (startPos, endPos) {
                | (Some(start), Some(end_)) =>
                  Some({
                    start,
                    end_,
                    source: None,
                  })
                | _ => None
                };
              | _ => None
              };
            })
       };
     });
};

/**
 * Convert raw JSON AST to our astNode structure
 */
let convertJsonToAstNode = (nodeJson: Js.Json.t): astNode => {
  let nodeTypeStr =
    nodeJson
    |> Js.Json.decodeObject
    |> Option.flatMap(obj => Js.Dict.get(obj, "type"))
    |> Option.flatMap(Js.Json.decodeString)
    |> Option.getOrElse("Unknown");

  let nodeType = convertNodeType(nodeTypeStr);
  let name = extractNodeName(nodeJson);
  let location = extractSourceLocation(nodeJson);

  // Extract children (this is simplified - real implementation would traverse based on node type)
  let children = [];

  {
    nodeType,
    name,
    location,
    children,
    metadata: nodeJson,
  };
};
let defaultParserDependencies: parserDependencies = {
  getCurrentTimestamp: () => Js.Date.now(),
  parseTypeScript: (sourceText, _config) => {
    // Convert our config to the format expected by TypeScript parser
    let fileName = "temp.ts"; // We could enhance this to pass actual filename
    Bindings.TypeScriptParser.parseTypeScript(sourceText, fileName);
  },
  parseJavaScript: (sourceText, config) => {
    // Convert our config to Babel options
    let babelOptions =
      Bindings.BabelParser.{
        sourceType: "module",
        allowImportExportEverywhere: config.allowImportExportEverywhere,
        allowReturnOutsideFunction: config.allowReturnOutsideFunction,
        allowNewTargetOutsideFunction: false,
        allowSuperOutsideMethod: false,
        allowUndeclaredExports: false,
        plugins: Array.fromList(config.plugins),
        strictMode: None,
        ranges: true,
        tokens: config.includeTokens,
        preserveComments: config.includeComments,
      };
    Bindings.BabelParser.parseJavaScript(sourceText, babelOptions);
  },
  convertToAstNode: jsonAst => {
    IO.pure(convertJsonToAstNode(jsonAst));
  },
};

/**
 * Determine parser type based on file extension
 */
let getParserType = (fileName: string): string => {
  switch (FileSystem.getFileExtension(fileName)) {
  | Some(".ts")
  | Some(".tsx") => "typescript"
  | Some(".js")
  | Some(".jsx")
  | Some(".mjs") => "javascript"
  | _ => "javascript" // Default to JavaScript parser
  };
};

let parseSourceCode =
    (
      sourceText: string,
      fileName: string,
      ~config: option(parserConfig)=?,
      ~deps: parserDependencies,
      (),
    )
    : IO.t(parseResult, Js.Exn.t) => {
  let startTime = deps.getCurrentTimestamp();
  let parserType = getParserType(fileName);
  let actualConfig =
    config
    |> Option.getOrElse(
         parserType === "typescript"
           ? defaultTypescriptConfig : defaultJavascriptConfig,
       );

  let parseOperation =
    parserType === "typescript"
      ? deps.parseTypeScript(sourceText, actualConfig)
      : deps.parseJavaScript(sourceText, actualConfig);

  parseOperation
  |> IO.flatMap(rawAst =>
       deps.convertToAstNode(rawAst)
       |> IO.map(ast => {
            let endTime = deps.getCurrentTimestamp();
            {
              ast,
              sourceText,
              fileName,
              parseTime: endTime -. startTime,
              parserUsed: parserType,
            };
          })
     );
};

/**
 * Extract specific types of nodes from AST
 */
let extractNodesByType = (ast: astNode, targetType: nodeType): list(astNode) => {
  let rec traverse = (node: astNode, acc: list(astNode)): list(astNode) => {
    let newAcc = node.nodeType === targetType ? [node, ...acc] : acc;
    List.foldLeft(
      (acc, child) => traverse(child, acc),
      newAcc,
      node.children,
    );
  };

  traverse(ast, []);
};

/**
 * Get all function definitions from AST
 */
let getFunctions = (ast: astNode): list(astNode) => {
  extractNodesByType(ast, Function);
};

/**
 * Get all class definitions from AST
 */
let getClasses = (ast: astNode): list(astNode) => {
  extractNodesByType(ast, Class);
};

/**
 * Get all import statements from AST
 */
let getImports = (ast: astNode): list(astNode) => {
  extractNodesByType(ast, Import);
};

/**
 * Get all export statements from AST
 */
let getExports = (ast: astNode): list(astNode) => {
  extractNodesByType(ast, Export);
};

/**
 * Generate summary of parsed code
 */
let getCodeSummary = (parseResult: parseResult): string => {
  let functions = getFunctions(parseResult.ast);
  let classes = getClasses(parseResult.ast);
  let imports = getImports(parseResult.ast);
  let exports = getExports(parseResult.ast);

  "File: "
  ++ parseResult.fileName
  ++ "\\n"
  ++ "Parser: "
  ++ parseResult.parserUsed
  ++ "\\n"
  ++ "Parse time: "
  ++ Float.toString(parseResult.parseTime)
  ++ "ms\\n"
  ++ "Functions: "
  ++ Int.toString(List.length(functions))
  ++ "\\n"
  ++ "Classes: "
  ++ Int.toString(List.length(classes))
  ++ "\\n"
  ++ "Imports: "
  ++ Int.toString(List.length(imports))
  ++ "\\n"
  ++ "Exports: "
  ++ Int.toString(List.length(exports));
};

/**
 * Parse a source file using default dependencies
 */
let parseFile =
    (filePath: string, ~config: option(parserConfig)=?, ())
    : IO.t(parseResult, Js.Exn.t) => {
  Bindings.NodeJs.Fs.readFileSync(filePath, `utf8)
  |> IO.flatMap(sourceText =>
       parseSourceCode(
         sourceText,
         filePath,
         ~config?,
         ~deps=defaultParserDependencies,
         (),
       )
     );
};

/**
 * Parse multiple files in parallel
 */
let parseFiles =
    (filePaths: list(string), ~config: option(parserConfig)=?, ())
    : IO.t(list(parseResult), Js.Exn.t) => {
  filePaths |> List.IO.traverse(filePath => parseFile(filePath, ~config?, ()));
};
