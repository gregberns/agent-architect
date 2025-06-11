open Relude.Globals;
open Bindings.NodeJs;

/**
 * Shared.re - Common types, encoders, decoders, and utilities for evaluation modules
 *
 * This module extracts shared functionality used across Ingest.re and Digest.re
 * to reduce duplication and increase reusability.
 */
/* ============================================================================
   SHARED TYPES AND MODULES
   ============================================================================ */
/* Prompt template specification */
module PromptTemplate = {
  type t = {
    name: string,
    hash: string,
    prompt: string,
  };

  let generateTemplateHash = (prompt_name, prompt_text): string => {
    // Simple hash based on template name and content
    prompt_name ++ ":" ++ prompt_text |> Utils.StringUtils.simpleHash;
  };

  let make = (~name, ~prompt) => {
    name,
    hash: generateTemplateHash(name, prompt),
    prompt,
  };

  let encode = (prompt: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("name", Js.Json.string(prompt.name)),
        ("hash", Js.Json.string(prompt.hash)),
        ("prompt", Js.Json.string(prompt.prompt)),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ name = field("name", string)
    and+ hash = Utils.JsonUtils.Decode.optionalField("hash", string)
    and+ prompt = field("prompt", string);
    {
      name,
      hash: hash |> Option.getOrElse(generateTemplateHash(name, prompt)),
      prompt,
    };
  };
};

/* JSON structure for prompt file */
module PromptFile = {
  type t = {prompts: array(PromptTemplate.t)};

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ prompts = field("prompts", array(PromptTemplate.decode));
    {prompts: prompts};
  };
};

/* Core evaluation task module */
module EvaluationTask = {
  type t = {
    text: string,
    code: string,
    task_id: int,
    test_setup_code: string,
    test_list: array(string),
    challenge_test_list: array(string),
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ text = field("text", string)
    and+ code = field("code", string)
    and+ task_id = field("task_id", intFromNumber)
    and+ test_setup_code = field("test_setup_code", string)
    and+ test_list = field("test_list", array(string))
    and+ challenge_test_list = field("challenge_test_list", array(string));
    {
      text,
      code,
      task_id,
      test_setup_code,
      test_list,
      challenge_test_list,
    };
  };

  let encode = (task: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("text", Js.Json.string(task.text)),
        ("code", Js.Json.string(task.code)),
        ("task_id", Js.Json.number(Float.fromInt(task.task_id))),
        ("test_setup_code", Js.Json.string(task.test_setup_code)),
        (
          "test_list",
          Js.Json.array(Array.map(Js.Json.string, task.test_list)),
        ),
        (
          "challenge_test_list",
          Js.Json.array(Array.map(Js.Json.string, task.challenge_test_list)),
        ),
      ]),
    );
  };
  let getTaskById = (tasks: array(t), taskId: int): option(t) => {
    Array.find(({task_id, _}: t) => task_id == taskId, tasks);
  };

  let filterTasksByTextContent =
      (tasks: array(t), searchTerm: string): array(t) => {
    Array.filter(
      ({text, _}: t) => String.contains(~search=searchTerm, text),
      tasks,
    );
  };

  let getTaskCount = (tasks: array(t)): int => {
    Array.length(tasks);
  };

  let getTasksWithTests = (tasks: array(t)): array(t) => {
    Array.filter(
      ({test_list, _}: t) => Array.length(test_list) > 0,
      tasks,
    );
  };

  let getTasksWithChallengeTests = (tasks: array(t)): array(t) => {
    Array.filter(
      ({challenge_test_list, _}: t) =>
        Array.length(challenge_test_list) > 0,
      tasks,
    );
  };

  let extractAllTestCases = (tasks: array(t)): array(string) => {
    Array.foldLeft(
      (acc, {test_list, challenge_test_list, _}: t) => {
        let allTests = Array.concat(test_list, challenge_test_list);
        Array.concat(acc, allTests);
      },
      [||],
      tasks,
    );
  };

  let validateTaskStructure = (task: t): bool => {
    String.trim(task.text) != ""
    && String.trim(task.code) != ""
    && task.task_id >= 0;
  };

  let validateAllTasks = (tasks: array(t)): (array(t), array(t)) => {
    Array.partition(validateTaskStructure, tasks);
  };

  let sortTasksByTaskId = (tasks: array(t)): array(t) => {
    Array.sortBy(
      ({task_id: a, _}: t, {task_id: b, _}: t) => Int.compare(a, b),
      tasks,
    );
  };

  let getTaskIds = (tasks: array(t)): array(int) => {
    Array.map(({task_id, _}: t) => task_id, tasks);
  };

  let getTasksInRange = (tasks: array(t), minId: int, maxId: int): array(t) => {
    Array.filter(
      ({task_id, _}: t) => task_id >= minId && task_id <= maxId,
      tasks,
    );
  };
};

/* Model response module */
module ModelResponse = {
  type t = {
    prompt: string,
    response: string,
    model_name: string,
    timestamp: float,
    invocation_index: option(int) // Optional for backward compatibility
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ prompt = field("prompt", string)
    and+ response = field("response", string)
    and+ model_name = field("model_name", string)
    and+ timestamp = field("timestamp", floatFromNumber)
    and+ invocation_index =
      optional(field("invocation_index", intFromNumber));
    {
      prompt,
      response,
      model_name,
      timestamp,
      invocation_index,
    };
  };

  let encode = (response: t): Js.Json.t => {
    let baseFields = [
      ("prompt", Js.Json.string(response.prompt)),
      ("response", Js.Json.string(response.response)),
      ("model_name", Js.Json.string(response.model_name)),
      ("timestamp", Js.Json.number(response.timestamp)),
    ];

    let allFields =
      switch (response.invocation_index) {
      | Some(index) => [
          ("invocation_index", Js.Json.number(Float.fromInt(index))),
          ...baseFields,
        ]
      | None => baseFields
      };

    Js.Json.object_(Js.Dict.fromList(allFields));
  };
};

/* Prompt result module */
module PromptResult = {
  type t = {
    promptTemplate: PromptTemplate.t,
    prompt: string,
    responses: array(ModelResponse.t),
    total_invocations: int,
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ promptTemplate = field("promptTemplate", PromptTemplate.decode)
    // template_name = field("template_name", string)
    // and+ template_hash = field("template_hash", string)
    and+ prompt = field("prompt", string)
    and+ responses = field("responses", array(ModelResponse.decode))
    and+ total_invocations = field("total_invocations", intFromNumber);
    {
      promptTemplate,
      prompt,
      responses,
      total_invocations,
    };
  };

  let encode = (promptResult: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        (
          "promptTemplate",
          promptResult.promptTemplate |> PromptTemplate.encode,
        ),
        ("prompt", Js.Json.string(promptResult.prompt)),
        (
          "responses",
          Js.Json.array(
            Array.map(ModelResponse.encode, promptResult.responses),
          ),
        ),
        (
          "total_invocations",
          Js.Json.number(Float.fromInt(promptResult.total_invocations)),
        ),
      ]),
    );
  };
};

/* Digest result module */
module DigestResult = {
  type t = {
    task: EvaluationTask.t,
    prompt_results: array(PromptResult.t),
    processing_time: float,
    processed_at: float,
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ task = field("task", EvaluationTask.decode)
    and+ prompt_results = field("prompt_results", array(PromptResult.decode))
    and+ processing_time = field("processing_time", floatFromNumber)
    and+ processed_at = field("processed_at", floatFromNumber);
    {
      task,
      prompt_results,
      processing_time,
      processed_at,
    };
  };

  let encode = (digestResult: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task", EvaluationTask.encode(digestResult.task)),
        (
          "prompt_results",
          Js.Json.array(
            Array.map(PromptResult.encode, digestResult.prompt_results),
          ),
        ),
        ("processing_time", Js.Json.number(digestResult.processing_time)),
        ("processed_at", Js.Json.number(digestResult.processed_at)),
      ]),
    );
  };
};

/* Extracted code module */
module ExtractedCode = {
  type t = {
    content: string,
    task_id: int,
    promptTemplate: PromptTemplate.t,
    invocation_index: int,
    response_index: int,
    file_path: string,
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ content = field("content", string)
    and+ task_id = field("task_id", intFromNumber)
    and+ promptTemplate = field("promptTemplate", PromptTemplate.decode)
    and+ invocation_index = field("invocation_index", intFromNumber)
    and+ response_index = field("response_index", intFromNumber)
    and+ file_path = field("file_path", string);
    {
      content,
      task_id,
      promptTemplate,
      invocation_index,
      response_index,
      file_path,
    };
  };

  let encode = (extracted: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("content", Js.Json.string(extracted.content)),
        ("task_id", Js.Json.number(Float.fromInt(extracted.task_id))),
        ("promptTemplate", extracted.promptTemplate |> PromptTemplate.encode),
        (
          "invocation_index",
          Js.Json.number(Float.fromInt(extracted.invocation_index)),
        ),
        (
          "response_index",
          Js.Json.number(Float.fromInt(extracted.response_index)),
        ),
        ("file_path", Js.Json.string(extracted.file_path)),
      ]),
    );
  };
};

/* Extraction result module */
module ExtractionResult = {
  type t = {
    extracted_files: array(ExtractedCode.t),
    total_files: int,
    processing_time: float,
    // Task metadata for evaluation
    task: EvaluationTask.t,
    executed_at: string, // ISO date string instead of JS float
    // Test execution data needed for CompilationCheck.re
    test_setup_code: string,
    test_list: array(string),
    challenge_test_list: array(string),
    // Prompt information for looking up template_hash
    prompt_results: array(PromptResult.t),
  };

  let encode = (result: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        (
          "extracted_files",
          Js.Json.array(
            Array.map(ExtractedCode.encode, result.extracted_files),
          ),
        ),
        ("total_files", Js.Json.number(Float.fromInt(result.total_files))),
        ("processing_time", Js.Json.number(result.processing_time)),
        ("task", EvaluationTask.encode(result.task)),
        ("executed_at", Js.Json.string(result.executed_at)),
        ("test_setup_code", Js.Json.string(result.test_setup_code)),
        (
          "test_list",
          Js.Json.array(Array.map(Js.Json.string, result.test_list)),
        ),
        (
          "challenge_test_list",
          Js.Json.array(
            Array.map(Js.Json.string, result.challenge_test_list),
          ),
        ),
        (
          "prompt_results",
          Js.Json.array(
            Array.map(PromptResult.encode, result.prompt_results),
          ),
        ),
      ]),
    );
  };
};

/* Compilation result module */
module CompilationResult = {
  type t = {
    extractedCode: ExtractedCode.t,
    file_path: string,
    runtimeError: list(string),
    parseError: list(string),
    compileError: list(string),
    testError: list(string),
    codeStyle: list(string),
  };

  let make =
      (
        ~extractedCode,
        ~file_path,
        ~runtimeError=[],
        ~parseError=[],
        ~compileError=[],
        ~testError=[],
        ~codeStyle=[],
        (),
      ) => {
    extractedCode,
    file_path,
    runtimeError,
    parseError,
    compileError,
    testError,
    codeStyle,
  };

  let encodeStringList = value =>
    Js.Json.array(List.map(Js.Json.string, value) |> List.toArray);

  let encode = (result: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("extractedCode", ExtractedCode.encode(result.extractedCode)),
        ("filePath", Js.Json.string(result.file_path)),
        ("runtimeError", result.runtimeError |> encodeStringList),
        ("parseError", result.parseError |> encodeStringList),
        ("compileError", result.compileError |> encodeStringList),
        ("testError", result.testError |> encodeStringList),
        ("codeStyle", result.codeStyle |> encodeStringList),
      ]),
    );
  };
  let decodeStringList: Utils.JsonUtils.Decode.t(list(string)) = {
    Utils.JsonUtils.Decode.(array(string) |> map(Array.toList));
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ extractedCode = field("extractedCode", ExtractedCode.decode)
    and+ file_path = field("filePath", string)
    and+ runtimeError = field("runtimeError", decodeStringList)
    and+ parseError = field("parseError", decodeStringList)
    and+ compileError = field("compileError", decodeStringList)
    and+ testError = field("testError", decodeStringList)
    and+ codeStyle = field("codeStyle", decodeStringList);
    {
      extractedCode,
      file_path,
      runtimeError,
      parseError,
      compileError,
      testError,
      codeStyle,
    };
  };

  let encodeArray = arr => Js.Json.array(Array.map(encode, arr));
};

/* Common error types for file and JSON operations */
type fileError = [
  | `FileReadError(Js.Exn.t)
  | `FileWriteError(Js.Exn.t)
];

type jsonlParseError = [
  | `FileReadError(Js.Exn.t)
  | `JsonParseError(string, string) // line, error message
  | `ValidationError(string, Utils.JsonUtils.ParseError.failure)
];

type processError = [
  fileError
  | jsonlParseError
  | `EncodingError(string)
  | `ValidationError(string, Utils.JsonUtils.ParseError.failure)
  | `CodeExtractionError(string)
  | `CompilationError(string)
  | `GradingError(string)
  | `DigestError(string)
  | `DirectoryCreationError(Js.Exn.t)
];

/* ============================================================================
   FILE OPERATIONS
   ============================================================================ */

module FileOps = {
  /* Read file contents */
  let readFileContents = (filePath: string): IO.t(string, Js.Exn.t) => {
    Fs.readFileSync(filePath, `utf8);
  };

  /* Write content to file */
  let writeFileContents =
      (filePath: string, content: string): IO.t(unit, Js.Exn.t) => {
    IO.triesJS(() => Node.Fs.writeFileAsUtf8Sync(filePath, content));
  };

  /* Append content to file */
  let appendToFile =
      (filePath: string, content: string): IO.t(unit, Js.Exn.t) => {
    readFileContents(filePath)
    |> IO.catchError(_ => IO.pure(""))  // File doesn't exist, start with empty
    |> IO.flatMap(existingContent => {
         let newContent =
           if (String.trim(existingContent) == "") {
             content;
           } else {
             existingContent ++ "\n" ++ content;
           };
         writeFileContents(filePath, newContent);
       });
  };

  /* Check if file exists */
  let fileExists = (filePath: string): IO.t(bool, Js.Exn.t) => {
    IO.triesJS(() => Node.Fs.existsSync(filePath));
  };
};

/* ============================================================================
   JSONL PROCESSING
   ============================================================================ */

module JsonlOps = {
  /* Split content by newlines and filter empty lines */
  let splitLines = (content: string): array(string) => {
    content
    |> String.splitList(~delimiter="\n")
    |> List.filter(line => String.trim(line) != "")
    |> List.toArray;
  };

  /* Parse a single JSON line */
  let parseJsonLine =
      (_lineNumber: int, line: string)
      : Result.t(EvaluationTask.t, jsonlParseError) => {
    switch (Utils.JsonUtils.parseSafe(line)) {
    | Some(json) =>
      switch (EvaluationTask.decode(json)) {
      | Result.Ok(task) => Result.Ok(task)
      | Result.Error(parseError) =>
        Result.Error(`ValidationError((line, parseError)))
      }
    | None => Result.Error(`JsonParseError((line, "Invalid JSON format")))
    };
  };

  /* Parse all lines in a JSONL content */
  let parseJsonlLines =
      (lines: array(string))
      : Result.t(array(EvaluationTask.t), list(jsonlParseError)) => {
    let results =
      Array.mapWithIndex(
        (line, index) => {
          let lineNumber = index + 1;
          parseJsonLine(lineNumber, line);
        },
        lines,
      );

    let (successes, errors) =
      Array.foldLeft(
        ((successAcc, errorAcc), result) => {
          switch (result) {
          | Result.Ok(task) => ([task, ...successAcc], errorAcc)
          | Result.Error(error) => (successAcc, [error, ...errorAcc])
          }
        },
        ([], []),
        results,
      );

    switch (errors) {
    | [] => Result.Ok(Array.fromList(List.reverse(successes)))
    | errorList => Result.Error(List.reverse(errorList))
    };
  };

  /* Read and parse JSONL file */
  let readJsonlFile =
      (filePath: string): IO.t(array(EvaluationTask.t), jsonlParseError) => {
    FileOps.readFileContents(filePath)
    |> IO.mapError(error => `FileReadError(error))
    |> IO.flatMap(content => {
         let lines = splitLines(content);
         switch (parseJsonlLines(lines)) {
         | Result.Ok(tasks) => IO.pure(tasks)
         | Result.Error([firstError, ..._rest]) => IO.throw(firstError)
         | Result.Error([]) => IO.pure([||]) // Empty file case
         };
       });
  };

  /* Write array of tasks to JSONL file */
  let writeJsonlFile =
      (filePath: string, tasks: array(EvaluationTask.t))
      : IO.t(unit, fileError) => {
    let jsonLines =
      Array.map(EvaluationTask.encode >> Js.Json.stringify, tasks);

    let content = Array.String.intercalate("\n", jsonLines);
    FileOps.writeFileContents(filePath, content)
    |> IO.mapError(error => `FileWriteError(error));
  };

  /* Append single task to JSONL file */
  let appendTaskToJsonl =
      (filePath: string, task: EvaluationTask.t): IO.t(unit, fileError) => {
    let json = EvaluationTask.encode(task);
    let jsonString = Js.Json.stringify(json);
    FileOps.appendToFile(filePath, jsonString)
    |> IO.mapError(error => `FileWriteError(error));
  };

  /* Append any JSON object to JSONL file */
  let appendJsonToJsonl =
      (filePath: string, json: Js.Json.t): IO.t(unit, fileError) => {
    let jsonString = Js.Json.stringify(json);
    FileOps.appendToFile(filePath, jsonString)
    |> IO.mapError(error => `FileWriteError(error));
  };
};

/* ============================================================================
   ERROR HANDLING UTILITIES
   ============================================================================ */

module ErrorUtils = {
  let jsonlParseErrorToString = (error: jsonlParseError): string => {
    switch (error) {
    | `FileReadError(jsError) =>
      "File read error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    | `JsonParseError(line, message) =>
      "JSON parse error on line '" ++ line ++ "': " ++ message
    | `ValidationError(line, _parseError) =>
      "Validation error on line '" ++ line ++ "': Invalid task structure"
    };
  };

  let fileErrorToString = (error: fileError): string => {
    switch (error) {
    | `FileReadError(jsError) =>
      "File read error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    | `FileWriteError(jsError) =>
      "File write error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    };
  };

  let processErrorToString = (error: processError): string => {
    switch (error) {
    | #fileError as fileErr => fileErrorToString(fileErr)
    | #jsonlParseError as jsonlErr => jsonlParseErrorToString(jsonlErr)
    | `EncodingError(msg) => "Encoding error: " ++ msg
    | `CodeExtractionError(msg) => "Code extraction error: " ++ msg
    | `CompilationError(msg) => "Compilation error: " ++ msg
    | `GradingError(msg) => "Grading error: " ++ msg
    | `DigestError(msg) => "Digest error: " ++ msg
    | `DirectoryCreationError(jsError) =>
      "Directory creation error: "
      ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
    };
  };
};

/* ============================================================================
   TASK UTILITIES
   ============================================================================ */

/* ============================================================================
   HIGH-LEVEL API FUNCTIONS
   ============================================================================ */

/* Load evaluation dataset with error handling */
let loadEvaluationDataset =
    (filePath: string): IO.t(array(EvaluationTask.t), string) => {
  JsonlOps.readJsonlFile(filePath)
  |> IO.mapError(ErrorUtils.jsonlParseErrorToString);
};

/* Save evaluation dataset */
let saveEvaluationDataset =
    (filePath: string, tasks: array(EvaluationTask.t)): IO.t(unit, string) => {
  JsonlOps.writeJsonlFile(filePath, tasks)
  |> IO.mapError(ErrorUtils.fileErrorToString);
};

/* Process evaluation file and print statistics */
let processEvaluationFile = (filePath: string): IO.t(unit, string) => {
  loadEvaluationDataset(filePath)
  |> IO.map(tasks => {
       let taskCount = EvaluationTask.getTaskCount(tasks);
       let tasksWithTests = EvaluationTask.getTasksWithTests(tasks);
       let testsWithChallenges =
         EvaluationTask.getTasksWithChallengeTests(tasks);

       Printf.printf("Loaded %d evaluation tasks\n", taskCount);
       Printf.printf(
         "Tasks with regular tests: %d\n",
         Array.length(tasksWithTests),
       );
       Printf.printf(
         "Tasks with challenge tests: %d\n",
         Array.length(testsWithChallenges),
       );
     });
};

/* Enhanced compilation results with evaluation metadata */
module CompilationResults = {
  type t = {
    compilation_results: array(CompilationResult.t),
    // Task metadata for evaluation
    task: EvaluationTask.t,
    executed_at: string,
    // Test execution data
    test_setup_code: string,
    test_list: array(string),
    challenge_test_list: array(string),
    // Prompt information for looking up template_hash
    prompt_results: array(PromptResult.t),
    total_files: int,
    processing_time: float,
  };

  let make =
      (
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
      )
      : t => {
    compilation_results,
    task,
    executed_at,
    test_setup_code,
    test_list,
    challenge_test_list,
    prompt_results,
    total_files,
    processing_time,
  };

  let encode = (results: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        (
          "compilation_results",
          Js.Json.array(
            Array.map(CompilationResult.encode, results.compilation_results),
          ),
        ),
        ("task", EvaluationTask.encode(results.task)),
        ("executed_at", Js.Json.string(results.executed_at)),
        ("test_setup_code", Js.Json.string(results.test_setup_code)),
        (
          "test_list",
          Js.Json.array(Array.map(Js.Json.string, results.test_list)),
        ),
        (
          "challenge_test_list",
          Js.Json.array(
            Array.map(Js.Json.string, results.challenge_test_list),
          ),
        ),
        (
          "prompt_results",
          Js.Json.array(
            Array.map(PromptResult.encode, results.prompt_results),
          ),
        ),
        ("total_files", Js.Json.number(Float.fromInt(results.total_files))),
        ("processing_time", Js.Json.number(results.processing_time)),
      ]),
    );
  };
};
