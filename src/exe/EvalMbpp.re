open Eval.Digest.DigestUtils;

// Create the input configuration using the new structure
let inputConfig =
  Eval.InputFileStructure.InputConfig.make(
    ~baseDir="/Users/gb/github/ai-experiments/agent-architect/data/evaluation",
    ~task_list_path=
      "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/source-data/mbpp.jsonl",
    ~task_range=
      Eval.InputFileStructure.TaskRange.make(~start_task=601, ~end_task=601),
    ~prompt_file_path=
      "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/prompts/prompts_001.json",
    ~prompt_iterations=2,
  );

let run = () => {
  Js.log("####### START #######");

  // Generate the evaluation run structure with loaded prompts
  Eval.InputFileStructure.generateEvaluationRun(~inputConfig)
  |> IO.flatMap(def =>
       Eval.InputFileStructure.saveEvaluationRun(def) |> IO.map(() => def)
     )
  |> IO.mapError(Eval.Shared.ErrorUtils.processErrorToString)
  |> IO.flatMap(
       (
         {input_config: {task_list_path, prompt_iterations, _}, task_paths, _} as evaluationRun: Eval.InputFileStructure.EvaluationRun.t,
       ) => {
       Js.log2("Using evaluation run structure:", evaluationRun);
       Js.log2("Task Paths:", task_paths);

       // Legacy variables for backward compatibility
       //  let inputPath = input_config.task_list_path;
       //  let taskId = 601;
       //  let promptIterations = input_config.prompt_iterations;
       task_paths
       |> Array.head
       |> Option.fold(
            Js.log("ERROR:: No task found") |> IO.pure,
            (
              {task_id, runs_file_path, _}: Eval.InputFileStructure.TaskPaths.t,
            ) =>
            digestSingleTaskById(
              ~modelName="",
              ~taskListPath=task_list_path,
              ~taskId=task_id,
              ~outputPath=runs_file_path,
              ~promptIterations=prompt_iterations,
              (),
            )
            |> IO.map(ignore)
          );
     })
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_r) => Js.log("####### OK #######")
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

run();
