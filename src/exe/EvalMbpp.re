let generateRunDefinition = () => {
  // Create the input configuration using the new structure
  let inputConfig =
    Eval.InputFileStructure.InputConfig.make(
      ~baseDir=
        "/Users/gb/github/ai-experiments/agent-architect/data/evaluation",
      ~task_list_path=
        "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/source-data/mbpp.jsonl",
      ~task_range=
        Eval.InputFileStructure.TaskRange.make(
          ~start_task=601,
          ~end_task=601,
        ),
      ~prompt_file_path=
        "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/prompts/prompts_001.json",
      ~prompt_iterations=2,
    );

  Js.log("####### START - Generate Run Definition #######");

  // Generate the evaluation run structure with loaded prompts
  Eval.InputFileStructure.generateEvaluationRun(~inputConfig)
  |> IO.flatMap(def =>
       Eval.InputFileStructure.saveEvaluationRun(def) |> IO.map(() => def)
     )
  |> IO.mapError(Eval.Shared.ErrorUtils.processErrorToString)
  // |> IO.flatMap(
  //      (
  //        {input_config: {task_list_path, prompt_iterations, _}, task_paths, _} as evaluationRun: Eval.InputFileStructure.EvaluationRun.t,
  //      ) => {
  //      Js.log2("Using evaluation run structure:", evaluationRun);
  //      Js.log2("Task Paths:", task_paths);
  //      // Legacy variables for backward compatibility
  //      //  let inputPath = input_config.task_list_path;
  //      //  let taskId = 601;
  //      //  let promptIterations = input_config.prompt_iterations;
  //      task_paths
  //      |> Array.head
  //      |> Option.fold(
  //           Js.log("ERROR:: No task found") |> IO.pure,
  //           (
  //             {task_id, runs_file_path, _}: Eval.InputFileStructure.TaskPaths.t,
  //           ) =>
  //           digestSingleTaskById(
  //             ~modelName="",
  //             ~taskListPath=task_list_path,
  //             ~taskId=task_id,
  //             ~outputPath=runs_file_path,
  //             ~promptIterations=prompt_iterations,
  //             (),
  //           )
  //           |> IO.map(ignore)
  //         );
  //    })
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_r) => Js.log("####### OK #######")
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

let runDefinition = runDefinitionPath => {
  Js.log("####### START - Run Definition #######");

  Eval.InputFileStructure.loadEvaluationRun(runDefinitionPath)
  |> IO.flatMap(
       (
         {
           input_config: {task_list_path: _, prompt_iterations: _, _},
           task_paths,
           prompts: _,
           _,
         } as evaluationRun: Eval.InputFileStructure.EvaluationRun.t,
       ) => {
       //  Js.log2("Using evaluation run structure:", evaluationRun);
       Js.log2("Task Paths:", task_paths);

       Eval.Digest.DigestUtils.digestEvaluationRun(
         ~modelName="",
         evaluationRun,
       )
       //  task_paths
       //  |> Array.head
       //  |> Option.fold(
       //       Js.log("ERROR:: No task found") |> IO.pure,
       //       (
       //         {task_id, runs_file_path, _}: Eval.InputFileStructure.TaskPaths.t,
       //       ) =>
       //       Eval.Digest.DigestUtils.digestSingleTaskById(
       //         ~modelName="",
       //         ~taskListPath=task_list_path,
       //         ~prompts,
       //         ~taskId=task_id,
       //         ~outputPath=runs_file_path,
       //         ~promptIterations=prompt_iterations,
       //         (),
       //       )
       //       |> IO.map(ignore)
       //     )
       |> IO.mapError(e => `DigestError(e));
     })
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_r) => Js.log("####### OK #######")
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

let postProcess =
    (
      {
        runs_file_path,
        scratch_dir_path,
        test_results_file_path,
        graded_results_file_path,
        _,
      }: Eval.InputFileStructure.TaskPaths.t,
    ) => {
  Js.log("=== Testing Process.re Code Extraction ===");
  Js.log("Digest file: " ++ runs_file_path);
  Js.log("Code file directory: " ++ scratch_dir_path);
  Js.log("Code validation results: " ++ test_results_file_path);
  Js.log("");

  Eval.GenerateFiles.processDigestFile(
    ~digestFilePath=runs_file_path,
    ~outputDir=scratch_dir_path,
  )
  |> IO.flatMap(
       Eval.CompilationCheck.checkFiles(
         ~compilePath=scratch_dir_path,
         ~codeValidationResultsPath=test_results_file_path,
       ),
     )
  |> IO.flatMap(Eval.GradeOutcome.gradeAndWrite(graded_results_file_path));
};

let runValidate = runDefinitionPath => {
  Eval.InputFileStructure.loadEvaluationRun(runDefinitionPath)
  |> IO.flatMap(({task_paths, _}: Eval.InputFileStructure.EvaluationRun.t) =>
       task_paths |> Array.IO.traverse(postProcess)
     )
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_) => {
           Js.log("$$$$$$$ Complete");
         }
       | Result.Error(error) => {
           Js.log2("❌ Extraction failed:", error);
         },
     );
};

let iteration = "001_2025-06-11_08-43-31";

let defPath = {j|/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/run-def/$iteration.json|j};

// generateRunDefinition();

// runDefinition(defPath);

runValidate(defPath);
