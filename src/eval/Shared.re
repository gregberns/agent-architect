open Relude.Globals;
open Bindings.NodeJs;

/**
 * Shared.re - Common types, encoders, decoders, and utilities for evaluation modules
 *
 * This module extracts shared functionality used across Ingest.re and Digest.re
 * to reduce duplication and increase reusability.
 */

/* ============================================================================
   SHARED TYPES
   ============================================================================ */

/* Core evaluation task type */
type evaluationTask = {
  text: string,
  code: string,
  task_id: int,
  test_setup_code: string,
  test_list: array(string),
  challenge_test_list: array(string),
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
];

/* ============================================================================
   JSON DECODERS
   ============================================================================ */

module Decode = {
  open Utils.JsonUtils.Decode;

  let evaluationTask: t(evaluationTask) = {
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
};

/* ============================================================================
   JSON ENCODERS
   ============================================================================ */

module Encode = {
  let evaluationTask = (task: evaluationTask): Js.Json.t => {
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

  let evaluationTaskArray = (tasks: array(evaluationTask)): Js.Json.t => {
    Js.Json.array(Array.map(evaluationTask, tasks));
  };
};

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
      : Result.t(evaluationTask, jsonlParseError) => {
    switch (Utils.JsonUtils.parseSafe(line)) {
    | Some(json) =>
      switch (Decode.evaluationTask(json)) {
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
      : Result.t(array(evaluationTask), list(jsonlParseError)) => {
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
      (filePath: string): IO.t(array(evaluationTask), jsonlParseError) => {
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
      (filePath: string, tasks: array(evaluationTask))
      : IO.t(unit, fileError) => {
    let jsonLines =
      Array.map(
        task => {
          let json = Encode.evaluationTask(task);
          Js.Json.stringify(json);
        },
        tasks,
      );

    let content = Array.String.intercalate("\n", jsonLines);
    FileOps.writeFileContents(filePath, content)
    |> IO.mapError(error => `FileWriteError(error));
  };

  /* Append single task to JSONL file */
  let appendTaskToJsonl =
      (filePath: string, task: evaluationTask): IO.t(unit, fileError) => {
    let json = Encode.evaluationTask(task);
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
    // | `ValidationError(line, _parseError) =>
    //   "Validation error on line '" ++ line ++ "': Invalid structure"
    };
  };
};

/* ============================================================================
   TASK UTILITIES
   ============================================================================ */

module TaskUtils = {
  let getTaskById =
      (tasks: array(evaluationTask), taskId: int): option(evaluationTask) => {
    Array.find(task => task.task_id == taskId, tasks);
  };

  let filterTasksByTextContent =
      (tasks: array(evaluationTask), searchTerm: string)
      : array(evaluationTask) => {
    Array.filter(
      task => String.contains(~search=searchTerm, task.text),
      tasks,
    );
  };

  let getTaskCount = (tasks: array(evaluationTask)): int => {
    Array.length(tasks);
  };

  let getTasksWithTests =
      (tasks: array(evaluationTask)): array(evaluationTask) => {
    Array.filter(task => Array.length(task.test_list) > 0, tasks);
  };

  let getTasksWithChallengeTests =
      (tasks: array(evaluationTask)): array(evaluationTask) => {
    Array.filter(task => Array.length(task.challenge_test_list) > 0, tasks);
  };

  let extractAllTestCases = (tasks: array(evaluationTask)): array(string) => {
    Array.foldLeft(
      (acc, task) => {
        let allTests = Array.concat(task.test_list, task.challenge_test_list);
        Array.concat(acc, allTests);
      },
      [||],
      tasks,
    );
  };

  let validateTaskStructure = (task: evaluationTask): bool => {
    String.trim(task.text) != ""
    && String.trim(task.code) != ""
    && task.task_id >= 0;
  };

  let validateAllTasks =
      (tasks: array(evaluationTask))
      : (array(evaluationTask), array(evaluationTask)) => {
    Array.partition(validateTaskStructure, tasks);
  };

  let sortTasksByTaskId =
      (tasks: array(evaluationTask)): array(evaluationTask) => {
    Array.sortBy((a, b) => Int.compare(a.task_id, b.task_id), tasks);
  };

  let getTaskIds = (tasks: array(evaluationTask)): array(int) => {
    Array.map(task => task.task_id, tasks);
  };

  let getTasksInRange =
      (tasks: array(evaluationTask), minId: int, maxId: int)
      : array(evaluationTask) => {
    Array.filter(
      task => task.task_id >= minId && task.task_id <= maxId,
      tasks,
    );
  };
};

/* ============================================================================
   HIGH-LEVEL API FUNCTIONS
   ============================================================================ */

/* Load evaluation dataset with error handling */
let loadEvaluationDataset =
    (filePath: string): IO.t(array(evaluationTask), string) => {
  JsonlOps.readJsonlFile(filePath)
  |> IO.mapError(ErrorUtils.jsonlParseErrorToString);
};

/* Save evaluation dataset */
let saveEvaluationDataset =
    (filePath: string, tasks: array(evaluationTask)): IO.t(unit, string) => {
  JsonlOps.writeJsonlFile(filePath, tasks)
  |> IO.mapError(ErrorUtils.fileErrorToString);
};

/* Process evaluation file and print statistics */
let processEvaluationFile = (filePath: string): IO.t(unit, string) => {
  loadEvaluationDataset(filePath)
  |> IO.map(tasks => {
       let taskCount = TaskUtils.getTaskCount(tasks);
       let tasksWithTests = TaskUtils.getTasksWithTests(tasks);
       let testsWithChallenges = TaskUtils.getTasksWithChallengeTests(tasks);

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
