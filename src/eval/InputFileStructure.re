open Relude.Globals;

/**
 * InputFileStructure.re - Data structures and utilities for managing evaluation file organization
 *
 * This module provides:
 * - Input parameter records for configuring evaluation runs
 * - Runtime data structures for organizing output files
 * - Path generation functions for consistent file organization
 * - Helper functions to generate the complete data structure
 */
/* ============================================================================
   INPUT PARAMETER TYPES
   ============================================================================ */
/* Task range specification */
module TaskRange = {
  type t = {
    start_task: int,
    end_task: int,
  };

  let make = (~start_task, ~end_task) => {
    start_task,
    end_task,
  };

  let encode = (range: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("start_task", Js.Json.number(Float.fromInt(range.start_task))),
        ("end_task", Js.Json.number(Float.fromInt(range.end_task))),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ start_task = field("start_task", intFromNumber)
    and+ end_task = field("end_task", intFromNumber);
    {
      start_task,
      end_task,
    };
  };
};

/* Prompt template specification */
module PromptTemplate = {
  type t = {
    template_name: string,
    template_hash: string,
    prompt_text: string,
  };

  let make = (~template_name, ~template_hash, ~prompt_text) => {
    template_name,
    template_hash,
    prompt_text,
  };

  let encode = (prompt: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("template_name", Js.Json.string(prompt.template_name)),
        ("template_hash", Js.Json.string(prompt.template_hash)),
        ("prompt_text", Js.Json.string(prompt.prompt_text)),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ template_name = field("template_name", string)
    and+ template_hash = field("template_hash", string)
    and+ prompt_text = field("prompt_text", string);
    {
      template_name,
      template_hash,
      prompt_text,
    };
  };
};

/* Input configuration for evaluation runs */
module InputConfig = {
  type t = {
    baseDir: string,
    task_list_path: string,
    task_range: TaskRange.t,
    prompt_file_path: string, // Path to JSON file containing prompt templates
    prompt_iterations: int,
  };

  let make =
      (
        ~baseDir,
        ~task_list_path,
        ~task_range,
        ~prompt_file_path,
        ~prompt_iterations,
      ) => {
    baseDir,
    task_list_path,
    task_range,
    prompt_file_path,
    prompt_iterations,
  };

  let encode = (config: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("baseDir", Js.Json.string(config.baseDir)),
        ("task_list_path", Js.Json.string(config.task_list_path)),
        ("task_range", TaskRange.encode(config.task_range)),
        ("prompt_file_path", Js.Json.string(config.prompt_file_path)),
        (
          "prompt_iterations",
          Js.Json.number(Float.fromInt(config.prompt_iterations)),
        ),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ baseDir = field("baseDir", string)
    and+ task_list_path = field("task_list_path", string)
    and+ task_range = field("task_range", TaskRange.decode)
    and+ prompt_file_path = field("prompt_file_path", string)
    and+ prompt_iterations = field("prompt_iterations", intFromNumber);
    {
      baseDir,
      task_list_path,
      task_range,
      prompt_file_path,
      prompt_iterations,
    };
  };
};

/* ============================================================================
   RUNTIME DATA STRUCTURE TYPES
   ============================================================================ */

/* File paths for a specific task */
module TaskPaths = {
  type t = {
    task_id: int,
    runs_file_path: string,
    scratch_dir_path: string,
    test_results_file_path: string,
    graded_results_file_path: string,
  };

  let make =
      (
        ~task_id,
        ~runs_file_path,
        ~scratch_dir_path,
        ~test_results_file_path,
        ~graded_results_file_path,
      ) => {
    task_id,
    runs_file_path,
    scratch_dir_path,
    test_results_file_path,
    graded_results_file_path,
  };

  let encode = (paths: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task_id", Js.Json.number(Float.fromInt(paths.task_id))),
        ("runs_file_path", Js.Json.string(paths.runs_file_path)),
        ("scratch_dir_path", Js.Json.string(paths.scratch_dir_path)),
        (
          "test_results_file_path",
          Js.Json.string(paths.test_results_file_path),
        ),
        (
          "graded_results_file_path",
          Js.Json.string(paths.graded_results_file_path),
        ),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ task_id = field("task_id", intFromNumber)
    and+ runs_file_path = field("runs_file_path", string)
    and+ scratch_dir_path = field("scratch_dir_path", string)
    and+ test_results_file_path = field("test_results_file_path", string)
    and+ graded_results_file_path = field("graded_results_file_path", string);
    {
      task_id,
      runs_file_path,
      scratch_dir_path,
      test_results_file_path,
      graded_results_file_path,
    };
  };
};

/* Complete evaluation run structure */
module EvaluationRun = {
  type t = {
    epoch: string,
    base_directory: string,
    input_config: InputConfig.t,
    runDefinitionPath: string,
    task_paths: array(TaskPaths.t),
    prompt_runs_file_path: string,
    prompts: array(PromptTemplate.t) // Loaded prompt templates
  };

  let make =
      (
        ~epoch,
        ~base_directory,
        ~input_config,
        ~runDefinitionPath,
        ~task_paths,
        ~prompt_runs_file_path,
        ~prompts,
      ) => {
    epoch,
    base_directory,
    input_config,
    runDefinitionPath,
    task_paths,
    prompt_runs_file_path,
    prompts,
  };

  let encode = (run: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("epoch", Js.Json.string(run.epoch)),
        ("base_directory", Js.Json.string(run.base_directory)),
        ("input_config", InputConfig.encode(run.input_config)),
        (
          "task_paths",
          Js.Json.array(Array.map(TaskPaths.encode, run.task_paths)),
        ),
        ("prompt_runs_file_path", Js.Json.string(run.prompt_runs_file_path)),
        (
          "prompts",
          Js.Json.array(Array.map(PromptTemplate.encode, run.prompts)),
        ),
      ]),
    );
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ epoch = field("epoch", string)
    and+ base_directory = field("base_directory", string)
    and+ input_config = field("input_config", InputConfig.decode)
    and+ runDefinitionPath = field("runDefinitionPath", string)
    and+ task_paths = field("task_paths", array(TaskPaths.decode))
    and+ prompt_runs_file_path = field("prompt_runs_file_path", string)
    and+ prompts = field("prompts", array(PromptTemplate.decode));
    {
      epoch,
      base_directory,
      input_config,
      runDefinitionPath,
      task_paths,
      prompt_runs_file_path,
      prompts,
    };
  };
};

/* ============================================================================
   PATH GENERATION FUNCTIONS
   ============================================================================ */

/* Generate epoch string from current time */
let generateEpoch = (): string => {
  let now = Js.Date.make();
  let year = Js.Date.getFullYear(now) |> Float.toInt |> string_of_int;
  let month =
    Js.Date.getMonth(now) |> Float.toInt |> (+)(1) |> Printf.sprintf("%02d");
  let day = Js.Date.getDate(now) |> Float.toInt |> Printf.sprintf("%02d");
  let hour = Js.Date.getHours(now) |> Float.toInt |> Printf.sprintf("%02d");
  let minute =
    Js.Date.getMinutes(now) |> Float.toInt |> Printf.sprintf("%02d");
  let second =
    Js.Date.getSeconds(now) |> Float.toInt |> Printf.sprintf("%02d");

  Printf.sprintf(
    "001_%s-%s-%s_%s-%s-%s",
    year,
    month,
    day,
    hour,
    minute,
    second,
  );
};

/* Generate runs file path for a specific task */
let generateRunsFilePath = (~baseDir, ~epoch, ~taskId): string => {
  Printf.sprintf("%s/outputs/runs/%s/task_%d.json", baseDir, epoch, taskId);
};

/* Generate scratch directory path for a specific task */
let generateScratchDirPath = (~baseDir, ~epoch, ~taskId): string => {
  Printf.sprintf("%s/outputs/scratch/%s/task_%d", baseDir, epoch, taskId);
};

/* Generate test results file path for a specific task */
let generateTestResultsFilePath = (~baseDir, ~epoch, ~taskId): string => {
  Printf.sprintf(
    "%s/outputs/test-results/%s/task_%d.json",
    baseDir,
    epoch,
    taskId,
  );
};

/* Generate graded results file path for a specific task */
let generateGradedResultsFilePath = (~baseDir, ~epoch, ~taskId): string => {
  Printf.sprintf(
    "%s/outputs/test-results-graded/%s/task_%d.json",
    baseDir,
    epoch,
    taskId,
  );
};

/* Generate prompt runs file path */
let generatePromptsFilePath = (~baseDir, ~epoch): string => {
  Printf.sprintf("%s/inputs/prompts/%s.json", baseDir, epoch);
};

let generateRunDefinitionFilePath = (~baseDir, ~epoch): string => {
  Printf.sprintf("%s/inputs/run-def/%s.json", baseDir, epoch);
};

/* ============================================================================
   PROMPT LOADING FUNCTIONS
   ============================================================================ */

/* JSON structure for prompt file */
module PromptFile = {
  type promptTemplate = {
    name: string,
    template: string,
  };

  type t = {prompts: array(promptTemplate)};

  let decodePromptTemplate: Utils.JsonUtils.Decode.t(promptTemplate) = {
    open Utils.JsonUtils.Decode;
    let+ name = field("name", string)
    and+ template = field("template", string);
    {
      name,
      template,
    };
  };

  let decode: Utils.JsonUtils.Decode.t(t) = {
    open Utils.JsonUtils.Decode;
    let+ prompts = field("prompts", array(decodePromptTemplate));
    {prompts: prompts};
  };
};

/* Load prompt templates from JSON file */
let loadPromptTemplates =
    (filePath: string): IO.t(array(PromptTemplate.t), Shared.processError) => {
  Shared.FileOps.readFileContents(filePath)
  |> IO.mapError(error => `FileReadError(error))
  |> IO.flatMap(content => {
       switch (Utils.JsonUtils.parseSafe(content)) {
       | Some(json) =>
         PromptFile.decode(json)
         |> Result.fold(
              e =>
                IO.throw(
                  `ValidationError((
                    "Failed to decode prompt file: " ++ filePath,
                    e,
                  )),
                ),
              ({prompts}: PromptFile.t) => {
                let prompts =
                  Array.mapWithIndex(
                    (promptTemplate, index) => {
                      let hash =
                        Printf.sprintf(
                          "%s_%d",
                          promptTemplate.PromptFile.name,
                          index,
                        );
                      PromptTemplate.make(
                        ~template_name=promptTemplate.PromptFile.name,
                        ~template_hash=hash,
                        ~prompt_text=promptTemplate.PromptFile.template,
                      );
                    },
                    prompts,
                  );
                IO.pure(prompts);
              },
            )
       | None =>
         IO.throw(
           `JsonParseError(("Invalid JSON in prompt file: " ++ filePath, "")),
         )
       }
     });
};

/* ============================================================================
   HELPER FUNCTIONS
   ============================================================================ */

let taskRange = (start_task, end_task) =>
  Int.eq(start_task, end_task)
    ? [|start_task|] : Int.rangeAsArray(start_task, end_task);

/* Generate task paths for a range of tasks */
let generateTaskPaths =
    (~baseDir, ~epoch, ~taskRange as {start_task, end_task}: TaskRange.t)
    : array(TaskPaths.t) => {
  taskRange(start_task, end_task)
  |> Array.map(taskId => {
       TaskPaths.make(
         ~task_id=taskId,
         ~runs_file_path=generateRunsFilePath(~baseDir, ~epoch, ~taskId),
         ~scratch_dir_path=generateScratchDirPath(~baseDir, ~epoch, ~taskId),
         ~test_results_file_path=
           generateTestResultsFilePath(~baseDir, ~epoch, ~taskId),
         ~graded_results_file_path=
           generateGradedResultsFilePath(~baseDir, ~epoch, ~taskId),
       )
     });
};

/* Generate complete evaluation run structure */
let generateEvaluationRun =
    (~inputConfig: InputConfig.t): IO.t(EvaluationRun.t, Shared.processError) => {
  let epoch = generateEpoch();
  let taskPaths =
    generateTaskPaths(
      ~baseDir=inputConfig.baseDir,
      ~epoch,
      ~taskRange=inputConfig.task_range,
    );
  let promptRunsFilePath =
    generatePromptsFilePath(~baseDir=inputConfig.baseDir, ~epoch);
  let runDefinitionFilePath =
    generateRunDefinitionFilePath(~baseDir=inputConfig.baseDir, ~epoch);

  loadPromptTemplates(inputConfig.prompt_file_path)
  |> IO.map(prompts => {
       EvaluationRun.make(
         ~epoch,
         ~base_directory=inputConfig.baseDir,
         ~input_config=inputConfig,
         ~runDefinitionPath=runDefinitionFilePath,
         ~task_paths=taskPaths,
         ~prompt_runs_file_path=promptRunsFilePath,
         ~prompts,
       )
     });
};

/* Generate evaluation run with custom epoch (for testing or specific naming) */
let generateEvaluationRunWithEpoch =
    (~baseDir, ~epoch, ~inputConfig: InputConfig.t)
    : IO.t(EvaluationRun.t, Shared.processError) => {
  let taskPaths =
    generateTaskPaths(~baseDir, ~epoch, ~taskRange=inputConfig.task_range);
  let promptRunsFilePath = generatePromptsFilePath(~baseDir, ~epoch);
  let runDefinitionFilePath =
    generateRunDefinitionFilePath(~baseDir=inputConfig.baseDir, ~epoch);

  loadPromptTemplates(inputConfig.prompt_file_path)
  |> IO.map(prompts => {
       EvaluationRun.make(
         ~epoch,
         ~base_directory=baseDir,
         ~input_config=inputConfig,
         ~runDefinitionPath=runDefinitionFilePath,
         ~task_paths=taskPaths,
         ~prompt_runs_file_path=promptRunsFilePath,
         ~prompts,
       )
     });
};

/* Save evaluation run structure to JSON file */
let saveEvaluationRun =
    (evaluationRun: EvaluationRun.t): IO.t(unit, Shared.processError) => {
  let jsonContent = evaluationRun |> EvaluationRun.encode |> Js.Json.stringify;

  Bindings.NodeJs.Fs.writeFileSyncRecursive(
    evaluationRun.prompt_runs_file_path,
    jsonContent,
    Bindings.NodeJs.Fs.makeWriteFileOptions(),
  )
  |> IO.mapError(error => `FileWriteError(error));
};

/* Load evaluation run structure from JSON file */
let loadEvaluationRun =
    (filePath: string): IO.t(EvaluationRun.t, Shared.processError) => {
  Shared.FileOps.readFileContents(filePath)
  |> IO.mapError(error => `FileReadError(error))
  |> IO.flatMap(content => {
       switch (Utils.JsonUtils.parseSafe(content)) {
       | Some(json) =>
         EvaluationRun.decode(json)
         |> Result.fold(
              e =>
                IO.throw(
                  `ValidationError((
                    "Failed to decode evaluation run: " ++ filePath,
                    e,
                  )),
                ),
              evaluationRun => IO.pure(evaluationRun),
            )
       | None =>
         IO.throw(
           `JsonParseError((
             "Invalid JSON in evaluation run file: " ++ filePath,
             "",
           )),
         )
       }
     });
};
