let generateRunDefinition = inputConfig => {
  // Create the input configuration using the new structure

  Js.log("####### START - Generate Run Definition #######");
  // Generate the evaluation run structure with loaded prompts
  Eval.InputFileStructure.generateEvaluationRun(~inputConfig)
  |> IO.flatMap(def =>
       Eval.InputFileStructure.saveEvaluationRun(def) |> IO.map(() => def)
     );
};
let generateRunDefinitionUnit = inputConfig => {
  generateRunDefinition(inputConfig)
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_) => Js.log("####### OK #######")
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

let runDefinition = runDefinitionPath => {
  Js.log("####### START - Run Definition #######");

  let apiKey =
    Bindings.NodeJs.Process.getEnvWithDefault(
      "OPENROUTER_API_KEY",
      "NOT VALID",
    );
  let model = "qwen/qwen-2.5-coder-32b-instruct";

  module OpenRouterModel =
    Model.Providers.OpenRouter({
      let model = model;
      let apiKey = apiKey;
      let temperature = 1.0;
    });

  module MyChat: Model.Chat.CHAT = Model.Chat.Chat(OpenRouterModel);

  Eval.InputFileStructure.loadEvaluationRun(runDefinitionPath)
  |> IO.flatMap(
       (
         {
           input_config: {task_list_path: _, prompt_iterations: _, _},
           task_paths: _,
           prompts: _,
           _,
         } as evaluationRun: Eval.InputFileStructure.EvaluationRun.t,
       ) => {
       Eval.Digest.DigestUtils.digestEvaluationRun(
         ~model=(module MyChat),
         evaluationRun,
       )
       |> IO.mapError(e => `DigestError(e))
     });
};
let runDefinitionUnit = runDefinitionPath => {
  runDefinition(runDefinitionPath)
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

let runValidate = (runDefinitionPath, epoch) => {
  Eval.InputFileStructure.loadEvaluationRun(runDefinitionPath)
  |> IO.flatMap(
       (
         {task_paths, summary_report_path, _}: Eval.InputFileStructure.EvaluationRun.t,
       ) =>
       task_paths
       |> Array.IO.traverse(postProcess)
       |> IO.flatMap(
            Eval.GradeOutcome.writeSummaryMarkdown(
              epoch,
              summary_report_path,
            ),
          )
     );
};

let runValidateUnit = (runDefinitionPath, epoch) => {
  runValidate(runDefinitionPath, epoch)
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

let defPath = epoch => {j|/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/run-def/$epoch.json|j};

let runAll = inputConfig =>
  generateRunDefinition(inputConfig)
  |> IO.flatMap(({epoch, _}: Eval.InputFileStructure.EvaluationRun.t) =>
       runDefinition(defPath(epoch))
       |> IO.flatMap(_ => runValidate(defPath(epoch), epoch))
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

// =================================================
// =================================================
// =================================================

let inputConfig =
  Eval.InputFileStructure.InputConfig.make(
    ~baseDir="/Users/gb/github/ai-experiments/agent-architect/data/evaluation",
    ~task_list_path=
      "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/source-data/mbpp.jsonl",
    ~task_range=
      Eval.InputFileStructure.TaskRange.make(~start_task=601, ~end_task=610),
    ~prompt_file_path=
      "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/prompts/prompts_003.json",
    ~prompt_iterations=2,
  );

// =================================================

// generateRunDefinitionUnit(inputConfig);

let epoch = "003_2025-06-17_08-42-05";

// runDefinitionUnit(defPath(epoch));

runValidateUnit(defPath(epoch), epoch);

// =================================================

// runAll(inputConfig);
