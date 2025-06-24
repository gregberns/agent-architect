open Relude.Globals;

/**
 * Digest.re - Process evaluation tests through model inference
 *
 * Workflow:
 * 1. Read in a single test
 * 2. Map over prompt list
 * 3. Traverse over (send to Model k times per prompt)
 * 4. Encode test + responses
 * 5. Write output to file
 *
 * Now supports running each prompt k times for evaluation consistency.
 */

/* Re-export shared types for backward compatibility */
type evaluationTask = Shared.EvaluationTask.t;

/* Types specific to digest processing */
// type promptTemplate = {
//   name: string,
//   template: string,
// };

module ModelResponse = {
  type t = {
    prompt: string,
    response: string,
    model_name: string,
    timestamp: float,
    invocation_index: int // Which invocation this is (0 to k-1)
  };

  let encode = (response: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("prompt", Js.Json.string(response.prompt)),
        ("response", Js.Json.string(response.response)),
        ("model_name", Js.Json.string(response.model_name)),
        ("timestamp", Js.Json.number(response.timestamp)),
        (
          "invocation_index",
          Js.Json.number(Float.fromInt(response.invocation_index)),
        ),
      ]),
    );
  };
};

module PromptResult = {
  type t = {
    promptTemplate: Shared.PromptTemplate.t,
    prompt: string,
    responses: array(ModelResponse.t), // All k responses for this prompt
    total_invocations: int,
  };

  let encode = (promptResult: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        (
          "promptTemplate",
          promptResult.promptTemplate |> Shared.PromptTemplate.encode,
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

module DigestResult = {
  type t = {
    task: evaluationTask,
    prompt_results: array(PromptResult.t), // Results for each prompt template
    processing_time: float,
    total_invocations: int // Total number of model calls made
  };

  let encode = (result: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task", Shared.EvaluationTask.encode(result.task)),
        (
          "prompt_results",
          Js.Json.array(
            Array.map(PromptResult.encode, result.prompt_results),
          ),
        ),
        ("processing_time", Js.Json.number(result.processing_time)),
        (
          "total_invocations",
          Js.Json.number(Float.fromInt(result.total_invocations)),
        ),
        ("processed_at", Js.Json.number(Js.Date.now())),
      ]),
    );
  };
};

type digestError = [
  | `ModelInvokeError(string)
  | `FileWriteError(Js.Exn.t)
  | `PromptGenerationError(string)
  | `EncodingError(string)
];

/* Model invoke function using loaded Gemini model */
let invokeModel =
    (~prompt: string, ~model: (module Model.Chat.CHAT)): IO.t(string, string) => {
  module Model = (val model);

  Model.init()
  |> IO.flatMap(m =>
       Model.sendMessage(
         m,
         ModelTypes.ModelInput.make1(ModelTypes.Message.makeUser(prompt)),
       )
     )
  |> IO.map(({text}: ModelTypes.AIMessageChunk.t) => text)
  |> IO.mapError((err: Model.err) =>
       err |> Model.errorToString |> Option.getOrElse("Unknown model error")
     );
};

/* Generate prompt from template and task */
let generatePrompt =
    (template: Shared.PromptTemplate.t, task: evaluationTask)
    : Result.t(string, string) => {
  // Replace {problem} placeholder
  let withText =
    String.replaceEach(
      ~search="{problem}",
      ~replaceWith=task.text,
      template.prompt,
    );

  // Replace {tests} placeholder if present
  let testsStr = Array.String.intercalate("\n", task.test_list);
  let withTests =
    String.replaceEach(~search="{tests}", ~replaceWith=testsStr, withText);

  // Replace {code} placeholder if present (for reference)
  let withCode =
    String.replaceEach(~search="{code}", ~replaceWith=task.code, withTests);

  Result.Ok(withCode);
};

/* Process single prompt k times */
let processPromptKTimes =
    (
      ~model: (module Model.Chat.CHAT),
      task: evaluationTask,
      template: Shared.PromptTemplate.t,
      k: int,
    )
    : IO.t(PromptResult.t, digestError) => {
  switch (generatePrompt(template, task)) {
  | Result.Ok(prompt) =>
    Int.rangeAsList(0, k)
    |> List.IO.traverse(invocationIndex => {
         invokeModel(~prompt, ~model)
         |> IO.mapError(error => `ModelInvokeError(error))
         |> IO.map((response): ModelResponse.t => {
              {
                prompt,
                response,
                model_name: "",
                timestamp: Js.Date.now(),
                invocation_index: invocationIndex,
              }
            })
       })
    |> IO.map((responseList): PromptResult.t => {
         {
           promptTemplate: template,
           prompt,
           responses: Array.fromList(responseList),
           total_invocations: k,
         }
       })
  // Create a list of invocation indices [0, 1, 2, ..., k-1]
  | Result.Error(error) => IO.throw(`PromptGenerationError(error))
  };
};

/* Process single test with multiple prompt templates, each run k times */
let processSingleTestWithK =
    (
      ~model: (module Model.Chat.CHAT),
      task: evaluationTask,
      prompts: array(Shared.PromptTemplate.t),
      promptIterations: int,
    )
    : IO.t(DigestResult.t, digestError) => {
  let startTime = Js.Date.now();
  Js.log2("  >> Complete - TaskId: ", task.task_id);

  // Map over prompt list and traverse over IO operations
  prompts
  |> Array.toList
  |> List.IO.traverse(template =>
       processPromptKTimes(
         ~model: (module Model.Chat.CHAT),
         task,
         template,
         promptIterations,
       )
     )
  |> IO.map((promptResultList): DigestResult.t => {
       let prompt_results = Array.fromList(promptResultList);
       let processingTime = Js.Date.now() -. startTime;
       let totalInvocations = Array.length(prompts) * promptIterations;

       {
         task,
         prompt_results,
         processing_time: processingTime,
         total_invocations: totalInvocations,
       };
     });
};

/* Write digest result to file using shared JSONL operations */
let writeDigestResult =
    (result: DigestResult.t, outputPath: string): IO.t(unit, digestError) => {
  DigestResult.encode(result)
  |> Js.Json.stringify
  |> Bindings.NodeJs.Fs.writeFileSyncRecursive(
       outputPath,
       _,
       Bindings.NodeJs.Fs.makeWriteFileOptions(),
     )
  |> IO.mapError(error => `FileWriteError(error));
};

/* Main digest processing function with k parameter */
let digestSingleTest =
    (
      ~model: (module Model.Chat.CHAT),
      ~prompts: array(Shared.PromptTemplate.t),
      ~outputPath: string,
      ~promptIterations: int=1, // Number of times to run each prompt
      task: evaluationTask,
      (),
    )
    : IO.t(DigestResult.t, digestError) =>
  processSingleTestWithK(~model, task, prompts, promptIterations)
  |> IO.flatMap(result => {
       Js.log2("  >> Complete - TaskId: ", task.task_id);
       writeDigestResult(result, outputPath) |> IO.map(_ => result);
     });

/* Batch processing functions with k parameter */
// let digestMultipleTests =
//     (
//       ~model: (module Model.Chat.CHAT),
//       ~prompts: array(Shared.PromptTemplate.t),
//       ~outputPath: string,
//       ~batchSize as _: int=5,
//       ~promptIterations: int=1, // Number of times to run each prompt
//       tasks: array(evaluationTask),
//       (),
//     )
//     : IO.t(array(DigestResult.t), digestError) =>
//   tasks
//   |> Array.toList
//   |> Utils.IOUtils.List.Sequential.traverse((task: evaluationTask) => {
//        Js.log2("  >> TaskId: ", task.task_id);
//        digestSingleTest(
//          ~model,
//          ~prompts,
//          ~outputPath,
//          ~promptIterations,
//          task,
//          (),
//        );
//      })
//   |> IO.map(Array.fromList);

/* Utility functions using shared implementations */
module DigestUtils = {
  // let loadAndDigestJsonl =
  //     (
  //       ~model: (module Model.Chat.CHAT),
  //       ~inputPath: string,
  //       ~prompts,
  //       ~outputPath: string,
  //       ~promptIterations: int=1,
  //       (),
  //     ) // Number of times to run each prompt
  //     : IO.t(array(DigestResult.t), string) => {
  //   // Use shared function to load evaluation dataset
  //   Shared.loadEvaluationDataset(inputPath)
  //   |> IO.tap(_ => Js.log("############ Loaded Data"))
  //   |> IO.flatMap(tasks => {
  //        digestMultipleTests(
  //          ~model,
  //          ~outputPath,
  //          ~prompts,
  //          ~promptIterations,
  //          tasks,
  //          (),
  //        )
  //        |> IO.mapError(error => {
  //             switch (error) {
  //             | `ModelInvokeError(msg) => "Model invoke error: " ++ msg
  //             | `FileWriteError(jsError) =>
  //               "File write error: "
  //               ++ (
  //                 Js.Exn.message(jsError)
  //                 |> Option.getOrElse("<<NO MESSAGE>>")
  //               )
  //             | `PromptGenerationError(msg) =>
  //               "Prompt generation error: " ++ msg
  //             | `EncodingError(msg) => "Encoding error: " ++ msg
  //             }
  //           })
  //      });
  // };

  // let digestSingleTaskById =
  //     (
  //       ~model: (module Model.Chat.CHAT),
  //       ~prompts,
  //       ~taskListPath: string,
  //       ~taskId: int,
  //       ~outputPath: string,
  //       ~promptIterations: int=1,
  //       (),
  //     ) // Number of times to run each prompt
  //     : IO.t(DigestResult.t, string) =>
  //   // Use shared function to load evaluation dataset
  //   Shared.loadEvaluationDataset(taskListPath)
  //   |> IO.tap(_ => Js.log("############ Loaded Data"))
  //   |> IO.flatMap(tasks =>
  //        Shared.EvaluationTask.getTaskById(tasks, taskId)
  //        |> Option.fold("Task Not Found" |> IO.throw, task =>
  //             digestSingleTest(
  //               ~model,
  //               ~prompts,
  //               ~outputPath,
  //               ~promptIterations,
  //               task,
  //               (),
  //             )
  //             |> IO.mapError(error =>
  //                  switch (error) {
  //                  | `ModelInvokeError(msg) => "Model invoke error: " ++ msg
  //                  | `FileWriteError(jsError) =>
  //                    "File write error: "
  //                    ++ (
  //                      Js.Exn.message(jsError)
  //                      |> Option.getOrElse("<<NO MESSAGE>>")
  //                    )
  //                  | `PromptGenerationError(msg) =>
  //                    "Prompt generation error: " ++ msg
  //                  | `EncodingError(msg) => "Encoding error: " ++ msg
  //                  }
  //                )
  //           )
  //      );
  //

  let mergeData = (task_paths, evaluationData) => {
    let tasks =
      task_paths
      |> Array.map(({task_id, _} as task: InputFileStructure.TaskPaths.t) =>
           (task_id, task)
         );

    let taskIds =
      task_paths
      |> Array.map(({task_id, _}: InputFileStructure.TaskPaths.t) => task_id);

    let evalData =
      evaluationData
      |> Array.filter(({task_id, _}: Shared.EvaluationTask.t) =>
           taskIds |> Array.Int.contains(task_id)
         )
      |> Array.map(({task_id, _} as task: Shared.EvaluationTask.t) =>
           (task_id, task)
         );

    Array.zipWith(
      ((_, task), (_, eval)) => (task, eval),
      tasks,
      evalData,
    );
  };

  let digestEvaluationRun =
      (
        ~model: (module Model.Chat.CHAT),
        {
          input_config: {task_list_path, prompt_iterations, _},
          task_paths,
          prompts,
          _,
        }: InputFileStructure.EvaluationRun.t,
      )
      : IO.t(array(DigestResult.t), string) => {
    // Use shared function to load evaluation dataset
    Shared.loadEvaluationDataset(task_list_path)
    |> IO.tap(_ => Js.log("############ Loaded Data"))
    |> IO.map(mergeData(task_paths))
    |> IO.flatMap(
         Array.toList
         >> Utils.IOUtils.List.Sequential.traverse(
              (
                (
                  {runs_file_path, _}: InputFileStructure.TaskPaths.t,
                  evalTask: Shared.EvaluationTask.t,
                ),
              ) => {
              digestSingleTest(
                ~model,
                ~outputPath=runs_file_path,
                ~prompts,
                ~promptIterations=prompt_iterations,
                evalTask,
                (),
              )
              |> IO.mapError(error =>
                   switch (error) {
                   | `ModelInvokeError(msg) => "Model invoke error: " ++ msg
                   | `FileWriteError(jsError) =>
                     "File write error: "
                     ++ (
                       Js.Exn.message(jsError)
                       |> Option.getOrElse("<<NO MESSAGE>>")
                     )
                   | `PromptGenerationError(msg) =>
                     "Prompt generation error: " ++ msg
                   | `EncodingError(msg) => "Encoding error: " ++ msg
                   }
                 )
            })
         >> IO.map(List.toArray),
       );
  };

  /* Analysis functions for k-repeated prompts */
  let analyzePromptConsistency = (promptResult: PromptResult.t): float => {
    // Calculate response consistency by comparing responses
    // For now, simple metric: ratio of unique responses to total responses
    let responses =
      Array.map(
        (response: ModelResponse.t) => response.response,
        promptResult.responses,
      );
    let uniqueResponses = String.Set.fromArray(responses) |> Set.length;
    Float.fromInt(uniqueResponses) /. Float.fromInt(Array.length(responses));
  };

  let getAverageResponseLength = (promptResult: PromptResult.t): float => {
    let totalLength =
      Array.foldLeft(
        (acc, response: ModelResponse.t) =>
          acc + String.length(response.response),
        0,
        promptResult.responses,
      );
    Float.fromInt(totalLength)
    /. Float.fromInt(Array.length(promptResult.responses));
  };

  let getBestResponse =
      (promptResult: PromptResult.t, ~scorer: string => float)
      : option(ModelResponse.t) => {
    // Find the response with the highest score according to the scorer function
    Array.maxBy(
      (response1: ModelResponse.t, response2: ModelResponse.t) =>
        Float.Ord.compare(
          scorer(response1.response),
          scorer(response2.response),
        ),
      promptResult.responses,
    );
  };
};

/* Convenience functions for common k values */
let digestSingleTestOnce = digestSingleTest(~promptIterations=1);
let digestSingleTestThrice = digestSingleTest(~promptIterations=3);
let digestSingleTestFiveTimes = digestSingleTest(~promptIterations=5);
let digestSingleTestTenTimes = digestSingleTest(~promptIterations=10);
