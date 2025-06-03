open Relude.Globals;

/**
 * Process.re - Extract and process code from digest results
 *
 * Phase 1: Extract code to files
 * - Read digest JSONL files
 * - Extract ReasonML code from responses
 * - Save to individual .re files with unique naming
 *
 * Phase 2: Check files for compilation errors
 * - Compile extracted .re files using Melange
 * - Collect and analyze compilation errors
 * - Generate error reports
 */

/* Type aliases for convenience */
type extractedCode = Shared.ExtractedCode.t;
type extractionResult = Shared.ExtractionResult.t;
type compilationResult = Shared.CompilationResult.t;
type processError = Shared.processError;

/* Code extraction utilities */
module CodeExtraction = {
  // let betweenMarkers = (~beginMarker, ~endMarker, str) =>
  //   Option.map2(
  //     (begin_, end_) =>
  //       String.slice(begin_ + String.length(beginMarker), end_, str),
  //     String.indexOf(~search=beginMarker, str),
  //     String.indexOf(~search=endMarker, str),
  //   )
  //   |> Option.getOrElse(str);
  // ;
  let betweenMarkers = (~beginMarker, ~endMarker, str) => {
    String.indexOf(~search=beginMarker, str)
    // Add the beginMarker spacing
    |> Option.map(i => i + String.length(beginMarker))
    |> Option.map(String.splitAt(_, str))
    |> Option.flatMap(((_, afterBeginMarker)) =>
         String.indexOf(~search=endMarker, afterBeginMarker)
         |> Option.map(String.splitAt(_, afterBeginMarker))
         |> Option.map(((beforeEndMarker, _)) => beforeEndMarker)
       )
    |> Option.getOrElse(str)//   (String.indexOf(~search=beginMarker, str) |> Option.getOrElse(0))
                             //   + String.length(beginMarker),
                             //   String.indexOf(~search=endMarker, str)
                             //   |> Option.getOrElse(String.length(str) - 1),
                             //   str,
                             ; // String.slice(
                             // );
  };

  /* Extract ReasonML code from response text */
  let extractReasonMLCode = (response: string): string => {
    // First, try to find code between [BEGIN] and [DONE] markers
    // let beginMarker = "[BEGIN]";
    // let endMarker = "[DONE]";
    let reasonmlBlock = "```reasonml";
    // let reasonBlock = "```reason";
    let genericBlock = "```";
    response
    // |> betweenMarkers(~beginMarker, ~endMarker)
    |> betweenMarkers(~beginMarker=reasonmlBlock, ~endMarker=genericBlock)
    // |> betweenMarkers(~beginMarker=reasonBlock, ~endMarker=genericBlock)
    // This will be probematic
    // |> betweenMarkers(~beginMarker=genericBlock, ~endMarker=genericBlock)
    |> String.trim;
    // If no [BEGIN]/[DONE] markers, try to extract from markdown code blocks
  };

  /* Generate file path for extracted code */
  let generateFilePath =
      (
        ~baseDir: string,
        ~taskId: int,
        ~templateHash: string,
        ~invocationIndex: int,
        ~responseIndex: int,
      )
      : string => {
    let taskDir = Printf.sprintf("%s/task_%d", baseDir, taskId);
    let filename =
      Printf.sprintf(
        "%s_%d_%d.re",
        templateHash,
        invocationIndex,
        responseIndex,
      );
    Printf.sprintf("%s/%s", taskDir, filename);
  };

  /* Create directory if it doesn't exist */
  let ensureDirectory = (dirPath: string): IO.t(unit, processError) =>
    // Create directory recursively
    Bindings.NodeJs.Fs.mkdirSync(
      dirPath,
      Bindings.NodeJs.Fs.mkdirOptions(~recursive=true, ()),
    )
    |> IO.mapError(error => `DirectoryCreationError(error));

  /* Write code to file */
  let writeCodeToFile =
      (filePath: string, code: string): IO.t(unit, processError) => {
    let dirPath = Node.Path.dirname(filePath);
    ensureDirectory(dirPath)
    |> IO.flatMap(_ => {
         IO.triesJS(() => Node.Fs.writeFileAsUtf8Sync(filePath, code))
         |> IO.mapError(error => `FileWriteError(error))
       });
  };
};

/* File processing functions */
module FileProcessing = {
  /* Read and parse digest file */
  let readDigestFile =
      (filePath: string): IO.t(Shared.DigestResult.t, processError) => {
    Shared.FileOps.readFileContents(filePath)
    |> IO.mapError(error => `FileReadError(error))
    |> IO.flatMap(content => {
         switch (Utils.JsonUtils.parseSafe(content)) {
         | Some(json) =>
           let decoded = Shared.DigestResult.decode(json);

           decoded
           |> Result.fold(
                e =>
                  IO.throw(
                    `JsonParseError((
                      "Failed to decode digest result: "
                      ++ (e |> BsDecode.Decode_ParseError.failureToDebugString),
                      "",
                    )),
                  ),
                digestResult => IO.pure(digestResult),
              );
         | None =>
           IO.throw(
             `JsonParseError(("Invalid JSON in file: " ++ filePath, "")),
           )
         }
       });
  };

  /* Extract code from digest result */
  let extractAllCode =
      (~baseDir, {prompt_results, task, _}: Shared.DigestResult.t)
      : extractionResult => {
    let startTime = Js.Date.now();

    let finalExtractedFiles =
      prompt_results
      |> Array.mapWithIndex(
           (promptResult: Shared.PromptResult.t, _promptIndex) =>
           promptResult.responses
           |> Array.mapWithIndex(
                (response: Shared.ModelResponse.t, responseIndex): Shared.ExtractedCode.t =>
                CodeExtraction.extractReasonMLCode(response.response)
                |> (
                  (code) => (
                    {
                      {
                        content: code,
                        task_id: task.task_id,
                        template_name: promptResult.template_name,
                        template_hash: promptResult.template_hash,
                        invocation_index:
                          response.invocation_index |> Option.getOrElse(0),
                        response_index: responseIndex,
                        file_path:
                          CodeExtraction.generateFilePath(
                            ~baseDir,
                            ~taskId=task.task_id,
                            ~templateHash=promptResult.template_hash,
                            ~invocationIndex=
                              response.invocation_index |> Option.getOrElse(0),
                            ~responseIndex,
                          ),
                      };
                    }: Shared.ExtractedCode.t
                  )
                )
              )
         )
      |> Array.flatten;

    {
      extracted_files: finalExtractedFiles,
      total_files: Array.length(finalExtractedFiles),
      processing_time: Js.Date.now() -. startTime,
    };
  };

  /* Write all extracted files to disk */
  let writeExtractedFiles =
      (extractedFiles: array(extractedCode)): IO.t(unit, processError) => {
    Array.IO.traverse(
      ({file_path, content, _}: extractedCode) =>
        CodeExtraction.writeCodeToFile(file_path, content),
      extractedFiles,
    )
    |> IO.map(_ => ());
  };
};

/* Compilation checking */
module CompilationCheck = {
  /* Create a dune file for compilation testing */
  let createDuneFile = (outputDir: string): IO.t(unit, processError) => {
    let duneContent = {|
(executable
 (public_name eval_test)
 (name main)
 (libraries relude melange.js melange.dom melange.node))

(rule
 (target compilation_report.txt)
 (deps (glob_files *.re))
 (action
  (with-outputs-to %{target}
   (system "dune build --profile dev 2>&1 || true"))))
|};

    let dunePath = Printf.sprintf("%s/dune", outputDir);
    CodeExtraction.writeCodeToFile(dunePath, duneContent);
  };

  /* Create a minimal main.re file */
  let createMainFile = (outputDir: string): IO.t(unit, processError) => {
    let mainContent = {|
(* Main file for compilation testing *)
let () = print_endline("Compilation test completed");
|};

    let mainPath = Printf.sprintf("%s/main.re", outputDir);
    CodeExtraction.writeCodeToFile(mainPath, mainContent);
  };

  /* Run compilation and collect errors */
  let compileFiles =
      (outputDir: string): IO.t(array(compilationResult), processError) => {
    createDuneFile(outputDir)
    |> IO.flatMap(_ => createMainFile(outputDir))
    |> IO.flatMap(_ => {
         IO.triesJS(() => {
           // Run dune build in the output directory
           let buildCommand =
             Printf.sprintf(
               "cd %s && dune build --profile dev 2>&1",
               outputDir,
             );
           let output =
             Node.Child_process.execSync(
               buildCommand,
               Node.Child_process.option(),
             );
           //  Js.String.castToJs(output);
           Js.String.make(output);
         })
         |> IO.mapError(error =>
              `CompilationError(
                Js.Exn.message(error)
                |> Option.getOrElse("Unknown compilation error"),
              )
            )
         |> IO.map(output => {
              // Parse compilation output to extract errors and warnings
              let lines = String.splitList(~delimiter="\n", output);
              let errors =
                List.filter(
                  line => String.contains(~search="Error:", line),
                  lines,
                );
              let warnings =
                List.filter(
                  line => String.contains(~search="Warning:", line),
                  lines,
                );

              [|
                (
                  {
                    file_path: outputDir,
                    success: List.length(errors) == 0,
                    errors: Array.fromList(errors),
                    warnings: Array.fromList(warnings),
                  }: compilationResult
                ),
              |];
            })
       });
  };
};

/* Main processing functions */
let processDigestFile =
    (~digestFilePath: string, ~outputDir: string)
    : IO.t(extractionResult, processError) => {
  Js.log("Reading digest file: " ++ digestFilePath);

  FileProcessing.readDigestFile(digestFilePath)
  |> IO.flatMap((digestResult: Shared.DigestResult.t) => {
       Js.log(
         "Found digest result for task "
         ++ string_of_int(digestResult.task.task_id),
       );

       FileProcessing.extractAllCode(~baseDir=outputDir, digestResult)
       |> (
         (
           {total_files, extracted_files, _} as extractionResult: extractionResult,
         ) => {
           Js.log(Printf.sprintf("Extracted %d code files", total_files));

           FileProcessing.writeExtractedFiles(extracted_files)
           |> IO.map(_ => extractionResult);
         }
       );
     });
};

let compileExtractedFiles =
    (~outputDir: string): IO.t(array(compilationResult), processError) => {
  CompilationCheck.compileFiles(outputDir);
};

/* High-level API functions */
let processAndCompile =
    (~digestFilePath: string, ~outputDir: string)
    : IO.t((extractionResult, array(compilationResult)), processError) => {
  processDigestFile(~digestFilePath, ~outputDir)
  |> IO.flatMap(extractionResult => {
       compileExtractedFiles(~outputDir)
       |> IO.map(compilationResults => (extractionResult, compilationResults))
     });
};

/* Error handling utilities */
module ErrorUtils = {
  let processErrorToString = Shared.ErrorUtils.processErrorToString;
};
