open Relude.Globals;
open Bindings.NodeJs;

/**
 * Process.re - JSONL file processing for evaluation data
 *
 * Reads .jsonl files and parses JSON objects with the structure:
 * {
 *   "text": "problem description",
 *   "code": "solution code",
 *   "task_id": number,
 *   "test_setup_code": "setup code",
 *   "test_list": ["test1", "test2"],
 *   "challenge_test_list": ["challenge_test1"]
 * }
 */

/* Types for the JSON structure */
type evaluationTask = {
  text: string,
  code: string,
  task_id: int,
  test_setup_code: string,
  test_list: array(string),
  challenge_test_list: array(string),
};

type jsonlParseError = [
  | `FileReadError(Js.Exn.t)
  | `JsonParseError(string, string) // line, error message
  | `ValidationError(string, Utils.JsonUtils.ParseError.failure)
];

/* JSON decoder for evaluationTask */
module Decode = {
  open Utils.JsonUtils.Decode;

  let evaluationTask: t(evaluationTask) = {
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
};

/* File reading helper */
let readFileContents = (filePath: string): IO.t(string, Js.Exn.t) => {
  Fs.readFileSync(filePath, `utf8);
};

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

/* Main function to read and parse JSONL file */
let readJsonlFile =
    (filePath: string): IO.t(array(evaluationTask), jsonlParseError) => {
  readFileContents(filePath)
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

/* Helper function to read JSONL file with error handling */
let readJsonlFileWithErrorHandling =
    (filePath: string): IO.t(array(evaluationTask), string) => {
  readJsonlFile(filePath)
  |> IO.mapError(error => {
       switch (error) {
       | `FileReadError(jsError) =>
         "File read error: "
         ++ (Js.Exn.message(jsError) |> Option.getOrElse("<<NO MESSAGE>>"))
       | `JsonParseError(line, message) =>
         "JSON parse error on line '" ++ line ++ "': " ++ message
       | `ValidationError(line, _parseError) =>
         "Validation error on line '" ++ line ++ "': Invalid task structure"
       }
     });
};

/* Utility functions for working with evaluation tasks */
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

  let extractAllTestCases = (tasks: array(evaluationTask)): array(string) =>
    Array.foldLeft(
      (acc, task) => {
        let allTests = Array.concat(task.test_list, task.challenge_test_list);
        Array.concat(acc, allTests);
      },
      [||],
      tasks,
    );
};

/* Example usage functions */
let loadEvaluationDataset =
    (filePath: string): IO.t(array(evaluationTask), string) => {
  readJsonlFileWithErrorHandling(filePath);
};

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

/* Validation helpers */
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
