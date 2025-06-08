/* Type aliases for convenience */
type extractedCode = Shared.ExtractedCode.t;
type extractionResult = Shared.ExtractionResult.t;
type compilationResult = Shared.CompilationResult.t;
type processError = Shared.processError;

// let run = buildCommand =>
//   Node.Child_process.execSync(buildCommand, Node.Child_process.option());

let tryRun = command =>
  Bindings.NodeJs.Child_process.exec(command)
  // |> IO.mapError(RJs.Exn.make)
  |> IO.summonError
  |> IO.mapError(_ => ());

module Parse = {
  let buildCommand = (~compilePath as _, compileFile) =>
    // Printf.sprintf("cd %s && refmt --print ml %s", compilePath, compileFile);
    Printf.sprintf("refmt --print ml %s", compileFile);

  let tryRun = (~compilePath, compileFile) =>
    buildCommand(~compilePath, compileFile) |> tryRun;
  // |> IO.tap(_ => Js.log2("  Compile - Parse: ", compileFile))
  // |> IO.tapError(_ => Js.log2("  Compile - Parse Error: ", compileFile));
};

module Compile = {
  let buildCommand = (~compilePath as _, compileFile) =>
    Printf.sprintf(
      // "cd %s && ocamlc -pp \"refmt --print ml\" -impl %s",
      "ocamlc -pp \"refmt --print ml\" -impl %s",
      // compilePath,
      compileFile,
    );

  let tryRun = (~compilePath, compileFile) =>
    buildCommand(~compilePath, compileFile) |> tryRun;
  // |> IO.tap(_ => Js.log2("  Compile - Compile: ", compileFile))
  // |> IO.tapError(_ => Js.log2("  Compile - Compile Error: ", compileFile));
};

module CodeValidation = {
  type t =
    // There was an issue parsing the code that provided. There could be multiple parsing errors.
    | ParseError(list(string))
    // The code was successfully parsed. One or more errors occured while attempting to compile the code.
    | CompileError(list(string))
    // The code was successfully parsed and compiled. The tests did not complete correctly.
    // There were differences between the expected output and the actual output.
    | TestErrors(list(string))
    // The test passed successfully. This captures potential improvements in best practices, code style, and libraries used.
    | CodeStyle(list(string));

  type process =
    | Stop(t)
    | Continue;
  let stop = result => Stop(result) |> IO.pure;
  let continue = () => Continue |> IO.pure;
};

let splitErrorString =
  String.splitAsList(~delimiter="\n\n")
  >> List.map(String.trim)
  >> List.filter(String.isNonEmpty);

/* Run compilation and collect errors */
let checkFile = (~compilePath: string, compileFile: string) =>
  // : IO.t(array(compilationResult), processError) =>
  Parse.tryRun(~compilePath, compileFile)
  |> IO.flatMap(
       fun
       | Result.Ok(_) => CodeValidation.continue()
       | Error(e) => CodeValidation.stop(ParseError(e |> splitErrorString)),
     )
  |> IO.flatMap(_ =>
       Compile.tryRun(~compilePath, compileFile)
       |> IO.flatMap(
            fun
            | Result.Ok(_) => CodeValidation.continue()
            | Error(e) =>
              CodeValidation.stop(CompileError(e |> splitErrorString)),
          )
     );

let checkFiles =
    (
      ~compilePath: string,
      ~codeValidationResultsPath: string,
      {extracted_files, _}: Shared.ExtractionResult.t,
    ) =>
  extracted_files
  |> Array.IO.traverse(({file_path, _} as extractedCode: extractedCode) => {
       let comp = Shared.CompilationResult.make(~extractedCode, ~file_path);
       checkFile(~compilePath, file_path)
       |> IO.map(
            fun
            | CodeValidation.Stop(res) =>
              switch (res) {
              | CodeValidation.ParseError(res) => comp(~parseError=res, ())
              | CompileError(res) => comp(~compileError=res, ())
              | TestErrors(res) => comp(~testError=res, ())
              | CodeStyle(res) => comp(~codeStyle=res, ())
              }
            | Continue => comp(),
          );
       //  |> IO.tap(_ => Js.log("$$$$$$$$$$$$$$$$$"));
     })
  |> IO.mapError(() =>
       RJs.Exn.make(
         "<<UNKNOWN ERROR FROM: " ++ __MODULE__ ++ ".checkFiles >>",
       )
     )
  |> IO.flatMap((x: array(compilationResult)) =>
       x
       |> Shared.CompilationResult.encodeArray
       |> Js.Json.stringify
       |> Bindings.NodeJs.Fs.writeFileSyncRecursive(
            codeValidationResultsPath ++ "/test.json",
            _,
            Bindings.NodeJs.Fs.makeWriteFileOptions(~flag=Write, ()),
          )
       |> IO.map(() => x)
     );
