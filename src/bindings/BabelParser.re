open Relude.Globals;

/**
 * Babel Parser Bindings
 *
 * Provides bindings to @babel/parser for JavaScript and JSX parsing.
 * Generates ESTree-compatible AST for JavaScript code analysis.
 */

/**
 * Babel parser options
 */
type babelParserOptions = {
  sourceType: string, // "module" | "script" | "unambiguous"
  allowImportExportEverywhere: bool,
  allowReturnOutsideFunction: bool,
  allowNewTargetOutsideFunction: bool,
  allowSuperOutsideMethod: bool,
  allowUndeclaredExports: bool,
  plugins: array(string),
  strictMode: option(bool),
  ranges: bool,
  tokens: bool,
  preserveComments: bool,
};

/**
 * Default Babel parser options for JavaScript
 */
let defaultJavaScriptOptions: babelParserOptions = {
  sourceType: "module",
  allowImportExportEverywhere: true,
  allowReturnOutsideFunction: false,
  allowNewTargetOutsideFunction: false,
  allowSuperOutsideMethod: false,
  allowUndeclaredExports: false,
  plugins: [|
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
  |],
  strictMode: None,
  ranges: true,
  tokens: false,
  preserveComments: true,
};

/**
 * Default Babel parser options for TypeScript (as fallback)
 */
let defaultTypeScriptOptions: babelParserOptions = {
  sourceType: "module",
  allowImportExportEverywhere: true,
  allowReturnOutsideFunction: false,
  allowNewTargetOutsideFunction: false,
  allowSuperOutsideMethod: false,
  allowUndeclaredExports: false,
  plugins: [|
    "typescript",
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
  |],
  strictMode: None,
  ranges: true,
  tokens: false,
  preserveComments: true,
};

/**
 * Raw Babel parser bindings
 */
module Raw = {
  // Main parse function
  [@bs.module "@babel/parser"] external parse': (string, 'a) => 'b = "parse";

  // Parse expression only
  external parseExpression': (string, 'a) => 'b = "parseExpression";

  // Convert AST to JSON
  [@bs.module] [@bs.scope "JSON"]
  external stringify: 'a => string = "stringify";
};

/**
 * Convert Babel options to JavaScript object for FFI
 */
let optionsToJs = (options: babelParserOptions): 'a => {
  let jsOptions = Js.Dict.empty();

  Js.Dict.set(jsOptions, "sourceType", Js.Json.string(options.sourceType));
  Js.Dict.set(
    jsOptions,
    "allowImportExportEverywhere",
    Js.Json.boolean(options.allowImportExportEverywhere),
  );
  Js.Dict.set(
    jsOptions,
    "allowReturnOutsideFunction",
    Js.Json.boolean(options.allowReturnOutsideFunction),
  );
  Js.Dict.set(
    jsOptions,
    "allowNewTargetOutsideFunction",
    Js.Json.boolean(options.allowNewTargetOutsideFunction),
  );
  Js.Dict.set(
    jsOptions,
    "allowSuperOutsideMethod",
    Js.Json.boolean(options.allowSuperOutsideMethod),
  );
  Js.Dict.set(
    jsOptions,
    "allowUndeclaredExports",
    Js.Json.boolean(options.allowUndeclaredExports),
  );
  Js.Dict.set(jsOptions, "plugins", Js.Json.stringArray(options.plugins));
  Js.Dict.set(jsOptions, "ranges", Js.Json.boolean(options.ranges));
  Js.Dict.set(jsOptions, "tokens", Js.Json.boolean(options.tokens));
  Js.Dict.set(
    jsOptions,
    "preserveComments",
    Js.Json.boolean(options.preserveComments),
  );

  // Add strictMode if specified
  switch (options.strictMode) {
  | Some(strict) =>
    Js.Dict.set(jsOptions, "strictMode", Js.Json.boolean(strict))
  | None => ()
  };

  jsOptions;
};

/**
 * IO-wrapped Babel operations
 */

/**
 * Parse JavaScript/TypeScript source code using Babel
 */
let parseJavaScript =
    (sourceText: string, options: babelParserOptions)
    : IO.t(Js.Json.t, Js.Exn.t) => {
  IO.triesJS(() => {
    let jsOptions = optionsToJs(options);
    let ast = Raw.parse'(sourceText, jsOptions);

    // Convert to JSON for consistent handling
    let jsonString = Raw.stringify(ast);
    Js.Json.parseExn(jsonString);
  });
};

/**
 * Parse JavaScript expression using Babel
 */
let parseExpression =
    (sourceText: string, options: babelParserOptions)
    : IO.t(Js.Json.t, Js.Exn.t) => {
  IO.triesJS(() => {
    let jsOptions = optionsToJs(options);
    let ast = Raw.parseExpression'(sourceText, jsOptions);

    // Convert to JSON for consistent handling
    let jsonString = Raw.stringify(ast);
    Js.Json.parseExn(jsonString);
  });
};

/**
 * Parse with automatic options selection based on file extension
 */
let parseWithAutoOptions =
    (sourceText: string, fileName: string): IO.t(Js.Json.t, Js.Exn.t) => {
  let getFileExtension = (filePath: string): option(string) => {
    let lastDotIndex = String.lastIndexOf(~search=".", filePath);
    switch (lastDotIndex) {
    | Some(index) => Some(String.sliceToEnd(index, filePath))
    | None => None
    };
  };

  let options =
    switch (getFileExtension(fileName)) {
    | Some(".ts")
    | Some(".tsx") => defaultTypeScriptOptions
    | _ => defaultJavaScriptOptions
    };

  parseJavaScript(sourceText, options);
};
/**
 * Check if file should be parsed with Babel (JavaScript files)
 */
let isJavaScriptFile = (fileName: string): bool => {
  let getFileExtension = (filePath: string): option(string) => {
    let lastDotIndex = String.lastIndexOf(~search=".", filePath);
    switch (lastDotIndex) {
    | Some(index) => Some(String.sliceToEnd(index, filePath))
    | None => None
    };
  };

  switch (getFileExtension(fileName)) {
  | Some(".js")
  | Some(".jsx")
  | Some(".mjs")
  | Some(".cjs") => true
  | _ => false
  };
};
/**
 * Get appropriate parser options for file type
 */
let getOptionsForFile = (fileName: string): babelParserOptions =>
  if (isJavaScriptFile(fileName)) {
    defaultJavaScriptOptions;
  } else {
    defaultTypeScriptOptions;
  };
