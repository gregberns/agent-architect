open Relude.Globals;

/**
 * TypeScript Compiler API Bindings
 *
 * Provides bindings to the TypeScript compiler for AST parsing and analysis.
 * Uses the official TypeScript npm package.
 */

/**
 * TypeScript compiler options for parsing
 */
type compilerOptions = {
  target: string, // "ES2015", "ES2017", etc.
  module_: string, // "CommonJS", "ES2015", etc.
  allowJs: bool,
  declaration: bool,
  sourceMap: bool,
  strict: bool,
};

/**
 * Script target enumeration
 */
module ScriptTarget = {
  [@bs.deriving abstract]
  type t = {
    [@bs.as "ES3"]
    es3: int,
    [@bs.as "ES5"]
    es5: int,
    [@bs.as "ES2015"]
    es2015: int,
    [@bs.as "ES2016"]
    es2016: int,
    [@bs.as "ES2017"]
    es2017: int,
    [@bs.as "ES2018"]
    es2018: int,
    [@bs.as "ES2019"]
    es2019: int,
    [@bs.as "ES2020"]
    es2020: int,
    [@bs.as "ESNext"]
    esNext: int,
    [@bs.as "Latest"]
    latest: int,
  };
};

/**
 * Module kind enumeration
 */
module ModuleKind = {
  [@bs.deriving abstract]
  type t = {
    [@bs.as "None"]
    none: int,
    [@bs.as "CommonJS"]
    commonJS: int,
    [@bs.as "AMD"]
    amd: int,
    [@bs.as "System"]
    system: int,
    [@bs.as "UMD"]
    umd: int,
    [@bs.as "ES2015"]
    es2015: int,
    [@bs.as "ES2020"]
    es2020: int,
    [@bs.as "ESNext"]
    esNext: int,
  };
};

/**
 * Default TypeScript compiler options
 */
let defaultCompilerOptions: compilerOptions = {
  target: "ES2017",
  module_: "ES2015",
  allowJs: true,
  declaration: false,
  sourceMap: false,
  strict: true,
};

/**
 * Raw TypeScript bindings
 */
module Raw = {
  // Create source file from text
  [@bs.module "typescript"]
  external createSourceFile': (string, string, int, bool) => 'a =
    "createSourceFile";

  // Parse configuration file
  [@bs.module "typescript"]
  external parseConfigFileTextToJson': (string, string) => 'a =
    "parseConfigFileTextToJson";

  // Create program from source files
  [@bs.module "typescript"]
  external createProgram': (array(string), 'a) => 'a = "createProgram";

  // Get source files from program
  [@bs.module "typescript"]
  external getSourceFiles': 'a => array('a) = "getSourceFiles";

  // Visit nodes in AST
  [@bs.module "typescript"]
  external forEachChild': ('a, 'a => unit) => unit = "forEachChild";

  // Get syntax kind constants
  // Get syntax kind constants - use a function to access the object
  [@bs.module "typescript"] [@bs.val]
  external getSyntaxKind: unit => 'a = "SyntaxKind";
  // Script target constants
  [@bs.module "typescript"] [@bs.val]
  external getScriptTarget: unit => ScriptTarget.t = "ScriptTarget";

  // Module kind constants
  [@bs.module "typescript"] [@bs.val]
  external getModuleKind: unit => ModuleKind.t = "ModuleKind";

  // Convert node to JSON for easier handling
  [@bs.module] [@bs.scope "JSON"]
  external stringify: 'a => string = "stringify";
};

/**
 * IO-wrapped TypeScript operations
 */

/**
 * Create a TypeScript source file from text
 */
let createSourceFile =
    (
      fileName: string,
      sourceText: string,
      languageVersion: int,
      setParentNodes: bool,
    )
    : IO.t('a, Js.Exn.t) => {
  IO.triesJS(() =>
    Raw.createSourceFile'(
      fileName,
      sourceText,
      languageVersion,
      setParentNodes,
    )
  );
};

/**
 * Parse TypeScript source code and return AST as JSON
 */
let parseTypeScript =
    (sourceText: string, fileName: string): IO.t(Js.Json.t, Js.Exn.t) => {
  // Use ES2017 target (value 4) and enable parent nodes for better traversal
  let languageVersion = 4; // ES2017

  createSourceFile(fileName, sourceText, languageVersion, true)
  |> IO.flatMap(sourceFile => {
       IO.triesJS(() => {
         // Convert the TypeScript AST to JSON for easier processing
         let jsonString = Raw.stringify(sourceFile);
         switch (Js.Json.parseExn(jsonString)) {
         | json => json
         | exception _ =>
           // Fallback: create a minimal AST structure
           Js.Json.object_(
             Js.Dict.fromList([
               ("type", Js.Json.string("Program")),
               ("body", Js.Json.array([||])),
               ("sourceType", Js.Json.string("module")),
             ]),
           )
         };
       })
     });
};

/**
 * Create a TypeScript program from multiple files
 */
let createProgram =
    (fileNames: array(string), options: compilerOptions): IO.t('a, Js.Exn.t) => {
  IO.triesJS(() => {
    // Convert our options to TypeScript format
    let tsOptions = Js.Dict.empty();
    Js.Dict.set(tsOptions, "target", Js.Json.string(options.target));
    Js.Dict.set(tsOptions, "module", Js.Json.string(options.module_));
    Js.Dict.set(tsOptions, "allowJs", Js.Json.boolean(options.allowJs));
    Js.Dict.set(
      tsOptions,
      "declaration",
      Js.Json.boolean(options.declaration),
    );
    Js.Dict.set(tsOptions, "sourceMap", Js.Json.boolean(options.sourceMap));
    Js.Dict.set(tsOptions, "strict", Js.Json.boolean(options.strict));

    Raw.createProgram'(fileNames, tsOptions);
  });
};

/**
 * Extract diagnostics from TypeScript program
 */
[@bs.module "typescript"]
external getPreEmitDiagnostics': 'a => array('a) = "getPreEmitDiagnostics";

let getDiagnostics = (program: 'a): IO.t(array('a), Js.Exn.t) => {
  IO.triesJS(() => getPreEmitDiagnostics'(program));
};
/**
 * Check if file is TypeScript based on extension
 */
let isTypeScriptFile = (fileName: string): bool => {
  let getFileExtension = (filePath: string): option(string) => {
    let lastDotIndex = String.lastIndexOf(~search=".", filePath);
    switch (lastDotIndex) {
    | Some(index) => Some(String.sliceToEnd(index, filePath))
    | None => None
    };
  };

  switch (getFileExtension(fileName)) {
  | Some(".ts")
  | Some(".tsx") => true
  | _ => false
  };
};
