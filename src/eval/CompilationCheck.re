/* Type aliases for convenience */
type extractedCode = Shared.ExtractedCode.t;
type extractionResult = Shared.ExtractionResult.t;
type compilationResult = Shared.CompilationResult.t;
type compilationResults = Shared.CompilationResults.t;
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
    buildCommand(~compilePath, compileFile)
    |> tryRun
    |> IO.mapError(() => RJs.Exn.make("Unknown error in Parse.tryRun"));
  // |> IO.tap(_ => Js.log3("  Compile - Parse: ", compilePath, compileFile))
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
    buildCommand(~compilePath, compileFile)
    |> tryRun
    |> IO.mapError(() => RJs.Exn.make("Unknown error in Compile.tryRun"));
  // |> IO.tap(_ => Js.log3("  Compile - Compile: ", compilePath, compileFile));
  // |> IO.tapError(_ => Js.log2("  Compile - Compile Error: ", compileFile));
};

module Build = {
  let duneFile: string = {j|(melange.emit
  (target example)
  (modules Task)
  (module_systems commonjs))|j};
  let duneProjectFile: string = {|(lang dune 3.8)
(using melange 0.1)|};

  let buildCommand = workDir => {j|cd $workDir && dune build --root=. --build-dir=./_build|j};
  let tryRun = (~compilePath, ~moduleName as _, _compileFile) => {
    let ( let* ) = IO.bind;

    let duneFilePath = compilePath ++ "/dune";
    let duneProjectPath = compilePath ++ "/dune-project";

    let* _ = Bindings.NodeJs.Fs.writeFileAsUtf8Sync(duneFilePath, duneFile);
    let* _ =
      Bindings.NodeJs.Fs.writeFileAsUtf8Sync(
        duneProjectPath,
        duneProjectFile,
      );

    buildCommand(compilePath)
    |> tryRun
    // |> IO.tap(Js.log2("$$$$$$$$$$$$$$$$$$$ "))
    |> IO.mapError(() => RJs.Exn.make("Unknown error in Build.tryRun"))
    // |> IO.tapError(_ => Js.log2("  Compile - Build Error: ", compileFile));
    // Result.Ok("thing") |> IO.pure;
  };
  // buildCommand |> tryRun;
  // |> IO.tap(_ => Js.log2("  Compile - Compile: ", compileFile))
};

module Test = {
  // data/evaluation/outputs/scratch/001_2025-06-11_08-43-31/task_601/T_1fcup3a_1_1/_build/default/example/Task.js
  let buildCommand = (compilePath, jsFilePath) => {j|cd $compilePath && node $jsFilePath|j};
  let tryRun = (~compilePath, ~moduleName as _, _compileFile) => {
    // Js.log3("  Test - Paths: ", compilePath, compileFile);
    // Js.log2("  Test - Module Name: ", moduleName);

    let jsFilePath = compilePath ++ "/_build/default/example/Task.js";

    buildCommand(compilePath, jsFilePath)
    |> tryRun
    // |> IO.tap(Js.log2("$$$$$$$$$$$$$$$$$$$ "))
    |> IO.mapError(() => RJs.Exn.make("Unknown error in Build.tryRun"));
  };
};

module CodeValidation = {
  type t =
    // There was an issue parsing the code that provided. There could be multiple parsing errors.
    | ParseError(list(string))
    // The code was successfully parsed. One or more errors occured while attempting to compile the code.
    | CompileError(list(string))
    // The code was successfully parsed and compiled. The tests did not complete correctly.
    // There were differences between the expected output and the actual output.
    | TestError(list(string))
    // The test passed successfully. This captures potential improvements in best practices, code style, and libraries used.
    | CodeStyle(list(string));

  type process =
    | Stop(t)
    | Continue;
  let stop = result => Stop(result) |> IO.pure;
  let continue = () => Continue |> IO.pure;
  let splitErrorString =
    String.splitAsList(~delimiter="\n\n")
    >> List.map(String.trim)
    >> List.filter(String.isNonEmpty);

  let parseError = e => ParseError(e |> splitErrorString);
  let compileError = e => CompileError(e |> splitErrorString);
  let testError = e => TestError(e |> splitErrorString);

  let ioWrapper = (onError, f) =>
    f
    |> IO.flatMap(
         fun
         | Result.Ok(_) => continue()
         | Error(e) => e |> onError |> stop,
       );

  let flatMap = f =>
    IO.flatMap(
      fun
      | Stop(t) => Stop(t) |> IO.pure
      | Continue => f,
    );
};

let getModuleName = (~compilePath, compileFile) =>
  String.replaceFirst(
    ~search=compilePath ++ "/",
    ~replaceWith="",
    compileFile,
  )
  |> String.replaceFirst(~search="/Task.re", ~replaceWith="");

/* Run compilation and collect errors */
let checkFile = (~compilePath: string, compileFile: string) => {
  let moduleName = getModuleName(~compilePath, compileFile);
  let compilePath = compilePath ++ "/" ++ moduleName;

  CodeValidation.ioWrapper(
    CodeValidation.parseError,
    Parse.tryRun(~compilePath, compileFile),
  )
  |> CodeValidation.flatMap(
       CodeValidation.ioWrapper(
         CodeValidation.compileError,
         Compile.tryRun(~compilePath, compileFile),
       ),
     )
  |> CodeValidation.flatMap(
       CodeValidation.ioWrapper(
         CodeValidation.compileError,
         Build.tryRun(~compilePath, ~moduleName, compileFile),
       ),
     )
  |> CodeValidation.flatMap(
       CodeValidation.ioWrapper(
         CodeValidation.testError,
         Test.tryRun(~compilePath, ~moduleName, compileFile),
       ),
     );
};

let checkFiles =
    (
      ~compilePath: string,
      ~codeValidationResultsPath: string,
      {
        extracted_files,
        task,
        executed_at,
        test_setup_code,
        test_list,
        challenge_test_list,
        prompt_results,
        total_files,
        processing_time,
        _,
      }: Shared.ExtractionResult.t,
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
              | TestError(res) => comp(~testError=res, ())
              | CodeStyle(res) => comp(~codeStyle=res, ())
              }
            | Continue => comp(),
          );
     })
  |> IO.flatMap((compilation_results: array(compilationResult)) => {
       let enhancedResults =
         Shared.CompilationResults.make(
           ~compilation_results,
           ~task,
           ~executed_at,
           ~test_setup_code,
           ~test_list,
           ~challenge_test_list,
           ~prompt_results,
           ~total_files,
           ~processing_time,
           (),
         );

       enhancedResults
       |> Shared.CompilationResults.encode
       |> Js.Json.stringify
       |> Bindings.NodeJs.Fs.writeFileSyncRecursive(
            codeValidationResultsPath,
            _,
            Bindings.NodeJs.Fs.makeWriteFileOptions(~flag=Write, ()),
          )
       |> IO.map(() => enhancedResults);
     })
  |> IO.mapError(e =>
       `CompilationError(
         e
         |> Js.Exn.message
         |> Option.getOrElse("<<NO COMPILE ERROR MESSAGE>>"),
       )
     );
