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

/* Types for processing digest files */
type extractedCode = {
  content: string,
  task_id: int,
  template_name: string,
  template_hash: string,
  invocation_index: int,
  response_index: int, // Which response from the k responses
  file_path: string,
};

type extractionResult = {
  extracted_files: array(extractedCode),
  total_files: int,
  processing_time: float,
};

type compilationResult = {
  file_path: string,
  success: bool,
  errors: array(string),
  warnings: array(string),
};

type processError = [
  | `FileReadError(Js.Exn.t)
  | `FileWriteError(Js.Exn.t)
  | `JsonParseError(string)
  | `CodeExtractionError(string)
  | `CompilationError(string)
  | `DirectoryCreationError(Js.Exn.t)
];

/* Decoder for digest result from Digest.re */
module DecodeDigest = {
  open Utils.JsonUtils.Decode;

  /* Decoder for the current format in test1.json */
  type currentFormatResponse = {
    prompt: string,
    response: string,
    model_name: string,
    timestamp: float,
  };

  let currentFormatResponse: t(currentFormatResponse) = {
    let+ prompt = field("prompt", string)
    and+ response = field("response", string)
    and+ model_name = field("model_name", string)
    and+ timestamp = field("timestamp", floatFromNumber);
    {
      prompt,
      response,
      model_name,
      timestamp,
    };
  };

  module FormatDigest = {
    type t = {
      task: Shared.evaluationTask,
      prompt_results: array(currentFormatResponse),
      processing_time: float,
      processed_at: float,
    };

    let decode: Utils.JsonUtils.Decode.t(t) = {
      let+ task = field("task", Shared.Decode.evaluationTask)
      and+ prompt_results =
        field("prompt_results", array(currentFormatResponse))
      and+ processing_time = field("processing_time", floatFromNumber)
      and+ processed_at = field("processed_at", floatFromNumber);
      {
        task,
        prompt_results,
        processing_time,
        processed_at,
      };
    };
  };
};

/* Code extraction utilities */
module CodeExtraction = {
  /* Extract ReasonML code from response text */
  let extractReasonMLCode = (response: string): option(string) => {
    // Look for code between [BEGIN] and [DONE] markers
    // let beginMarker = "[BEGIN]";
    // let endMarker = "[DONE]";
    response
    // String.slice(
    //   String.indexOf(~search=beginMarker, response) |> Option.getOrElse(0),
    //   String.indexOf(~search=endMarker, response)
    //   |> Option.getOrElse(response |> String.length),
    //   response,
    // )
    // |> String.trim
    |> Option.pure;
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
  /* Read and parse digest file (single JSON object format) */
  let readDigestFile =
      (filePath: string): IO.t(DecodeDigest.FormatDigest.t, processError) => {
    Shared.FileOps.readFileContents(filePath)
    |> IO.mapError(error => `FileReadError(error))
    |> IO.flatMap(content => {
         switch (Utils.JsonUtils.parseSafe(content)) {
         | Some(json) =>
           switch (DecodeDigest.FormatDigest.decode(json)) {
           | Result.Ok(digestResult) => IO.pure(digestResult)
           | Result.Error(e) =>
             IO.throw(
               `JsonParseError(
                 "Failed to decode digest result"
                 ++ (e |> BsDecode.Decode_ParseError.failureToDebugString),
               ),
             )
           }
         | None =>
           IO.throw(`JsonParseError("Invalid JSON in file: " ++ filePath))
         }
       });
  };
  /* Extract code from current format digest result */
  let extractAllCode =
      (~baseDir, {prompt_results, task, _}: DecodeDigest.FormatDigest.t)
      : IO.t(extractionResult, processError) => {
    let startTime = Js.Date.now();
    let extractedFiles = ref([]);

    prompt_results
    |> Array.forEachWithIndex(
         (
           {response, prompt, _}: DecodeDigest.currentFormatResponse,
           responseIndex,
         ) => {
         switch (CodeExtraction.extractReasonMLCode(response)) {
         | Some(code) =>
           /* Generate a simple hash from the prompt for file naming */
           let promptHash = prompt |> Utils.StringUtils.simpleHash;

           let filePath =
             CodeExtraction.generateFilePath(
               ~baseDir,
               ~taskId=task.task_id,
               ~templateHash=promptHash,
               ~invocationIndex=0, // Default since current format doesn't have invocation index
               ~responseIndex,
             );

           let extractedCode = {
             content: code,
             task_id: task.task_id,
             template_name: "prompt_" ++ string_of_int(responseIndex), // Simple template name
             template_hash: promptHash,
             invocation_index: 0,
             response_index: responseIndex,
             file_path: filePath,
           };

           extractedFiles := [extractedCode, ...extractedFiles^];
         | None => () // Skip responses without extractable code
         }
       });

    let finalExtractedFiles = Array.fromList(List.reverse(extractedFiles^));
    let processingTime = Js.Date.now() -. startTime;

    IO.pure({
      extracted_files: finalExtractedFiles,
      total_files: Array.length(finalExtractedFiles),
      processing_time: processingTime,
    });
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
                {
                  file_path: outputDir,
                  success: List.length(errors) == 0,
                  errors: Array.fromList(errors),
                  warnings: Array.fromList(warnings),
                },
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
  |> IO.flatMap((digestResult: DecodeDigest.FormatDigest.t) => {
       Js.log(
         "Found digest result for task "
         ++ string_of_int(digestResult.task.task_id),
       );

       FileProcessing.extractAllCode(~baseDir=outputDir, digestResult)
       |> IO.flatMap(extractionResult => {
            Js.log(
              Printf.sprintf(
                "Extracted %d code files",
                extractionResult.total_files,
              ),
            );

            FileProcessing.writeExtractedFiles(
              extractionResult.extracted_files,
            )
            |> IO.map(_ => extractionResult);
          });
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
  let processErrorToString = (error: processError): string => {
    switch (error) {
    | `FileReadError(jsError) =>
      "File read error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    | `FileWriteError(jsError) =>
      "File write error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    | `JsonParseError(msg) => "JSON parse error: " ++ msg
    | `CodeExtractionError(msg) => "Code extraction error: " ++ msg
    | `CompilationError(msg) => "Compilation error: " ++ msg
    | `DirectoryCreationError(jsError) =>
      "Directory creation error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    };
  };
};
