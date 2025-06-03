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
type evaluationTask = Shared.evaluationTask;

/* Types specific to digest processing */
type promptTemplate = {
  name: string,
  template: string,
};

type modelResponse = {
  prompt: string,
  response: string,
  model_name: string,
  timestamp: float,
  invocation_index: int // Which invocation this is (0 to k-1)
};
type promptResult = {
  template_name: string,
  template_hash: string, // Unique hash of the prompt template for identification
  prompt: string,
  responses: array(modelResponse), // All k responses for this prompt
  total_invocations: int,
};

type digestResult = {
  task: evaluationTask,
  prompt_results: array(promptResult), // Results for each prompt template
  processing_time: float,
  total_invocations: int // Total number of model calls made
};

type digestError = [
  | `ModelInvokeError(string)
  | `FileWriteError(Js.Exn.t)
  | `PromptGenerationError(string)
  | `EncodingError(string)
];

/* Model integration setup */
module Chat = (Model: ModelTypes.Model.MODEL) => {
  let init = () => Model.make();

  let sendMessage = (model, message: ModelTypes.ModelInput.t) =>
    Model.invoke(model, message);
};

let googleApiKey =
  Bindings.NodeJs.Process.getEnvWithDefault("GOOGLE_API_KEY", "NOT VALID");
let gemini_2_0_flash = "gemini-2.0-flash";

module LoadedGeminiModel =
  Model.Gemini.Model({
    let model = gemini_2_0_flash;
    let apiKey = googleApiKey;
    let temperature = 1.0;
  });

module MyChat = Chat(LoadedGeminiModel);

/* Model invoke function using loaded Gemini model */
let invokeModel =
    (~prompt: string, ~modelName as _: string): IO.t(string, string) =>
  MyChat.init()
  |> IO.flatMap(
       MyChat.sendMessage(
         _,
         ModelTypes.ModelInput.make1(ModelTypes.Message.makeUser(prompt)),
       ),
     )
  |> IO.map(({text}: ModelTypes.AIMessageChunk.t) => text)
  |> IO.mapError(Js.Exn.message >> Option.getOrElse("Unknown model error"));

/* Generate a unique hash for a prompt template */
let generateTemplateHash = (template: promptTemplate): string => {
  // Simple hash based on template name and content
  let content = template.name ++ ":" ++ template.template;

  content |> Utils.StringUtils.simpleHash;
};

/* Default prompt templates for code evaluation */
module PromptTemplates = {
  let basicCodeGeneration: promptTemplate = {
    name: "basic_code_generation",
    template: "You are an expert ReasonML programmer, and here is your task: {problem} Your ReasonML code should pass these tests:\n\n{tests}\n[BEGIN]\n{code}\n[DONE]",
  };

  let codeWithTests: promptTemplate = {
    name: "code_with_tests",
    template: "You are learning ReasonML, and here is your task: {problem} Write ReasonML code to pass these tests:\n\n{tests}\n[BEGIN]\n{code}\n[DONE]",
  };

  let defaultTemplates: array(promptTemplate) = [|
    basicCodeGeneration,
    codeWithTests,
  |];
};

/* Generate prompt from template and task */
let generatePrompt =
    (template: promptTemplate, task: evaluationTask)
    : Result.t(string, string) => {
  // Replace {problem} placeholder
  let withText =
    String.replaceEach(
      ~search="{problem}",
      ~replaceWith=task.text,
      template.template,
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
      task: evaluationTask,
      template: promptTemplate,
      modelName: string,
      k: int,
    )
    : IO.t(promptResult, digestError) => {
  switch (generatePrompt(template, task)) {
  | Result.Ok(prompt) =>
    // Create a list of invocation indices [0, 1, 2, ..., k-1]
    let invocationIndices = Int.rangeAsList(0, k);

    List.IO.traverse(
      invocationIndex => {
        invokeModel(~prompt, ~modelName)
        |> IO.mapError(error => `ModelInvokeError(error))
        |> IO.map(response => {
             {
               prompt,
               response,
               model_name: modelName,
               timestamp: Js.Date.now(),
               invocation_index: invocationIndex,
             }
           })
      },
      invocationIndices,
    )
    |> IO.map(responseList => {
         let responses = Array.fromList(responseList);
         {
           template_name: template.name,
           template_hash: generateTemplateHash(template),
           prompt,
           responses,
           total_invocations: k,
         };
       });
  | Result.Error(error) => IO.throw(`PromptGenerationError(error))
  };
};

/* Process single test with multiple prompt templates, each run k times */
let processSingleTestWithK =
    (
      task: evaluationTask,
      prompts: array(promptTemplate),
      modelName: string,
      promptIterations: int,
    )
    : IO.t(digestResult, digestError) => {
  let startTime = Js.Date.now();

  // Map over prompt list and traverse over IO operations
  List.IO.traverse(
    template =>
      processPromptKTimes(task, template, modelName, promptIterations),
    Array.toList(prompts),
  )
  |> IO.map(promptResultList => {
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

/* Encode digest result to JSON using shared encoder for evaluation task */
module EncodeDigest = {
  let encodeModelResponse = (response: modelResponse): Js.Json.t => {
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

  let encodePromptResult = (promptResult: promptResult): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("template_name", Js.Json.string(promptResult.template_name)),
        ("template_hash", Js.Json.string(promptResult.template_hash)),
        ("prompt", Js.Json.string(promptResult.prompt)),
        (
          "responses",
          Js.Json.array(
            Array.map(encodeModelResponse, promptResult.responses),
          ),
        ),
        (
          "total_invocations",
          Js.Json.number(Float.fromInt(promptResult.total_invocations)),
        ),
      ]),
    );
  };

  // Use shared encoder for evaluation task
  let encodeEvaluationTask = Shared.Encode.evaluationTask;

  let encodeDigestResult = (result: digestResult): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task", encodeEvaluationTask(result.task)),
        (
          "prompt_results",
          Js.Json.array(
            Array.map(encodePromptResult, result.prompt_results),
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

/* Write digest result to file using shared JSONL operations */
let writeDigestResult =
    (result: digestResult, outputPath: string): IO.t(unit, digestError) => {
  let jsonContent = EncodeDigest.encodeDigestResult(result);
  Shared.JsonlOps.appendJsonToJsonl(outputPath, jsonContent)
  |> IO.mapError(error => {
       switch (error) {
       | `FileWriteError(jsError) => `FileWriteError(jsError)
       | `FileReadError(jsError) => `FileWriteError(jsError) // Convert read error to write error for consistency
       }
     });
};

/* Main digest processing function with k parameter */
let digestSingleTest =
    (
      ~prompts: array(promptTemplate)=PromptTemplates.defaultTemplates,
      ~modelName: string,
      ~outputPath: string,
      ~promptIterations: int=1, // Number of times to run each prompt
      task: evaluationTask,
      (),
    )
    : IO.t(digestResult, digestError) => {
  Js.log(
    "    #### Task: "
    ++ (task.task_id |> Int.toString)
    ++ " (k="
    ++ (promptIterations |> Int.toString)
    ++ ")",
  );
  processSingleTestWithK(task, prompts, modelName, promptIterations)
  |> IO.flatMap(result => {
       writeDigestResult(result, outputPath) |> IO.map(_ => result)
     });
};

/* Batch processing functions with k parameter */
let digestMultipleTests =
    (
      ~prompts: array(promptTemplate)=PromptTemplates.defaultTemplates,
      ~modelName: string,
      ~outputPath: string,
      ~batchSize: int=5,
      ~promptIterations: int=1, // Number of times to run each prompt
      tasks: array(evaluationTask),
      (),
    )
    : IO.t(array(digestResult), digestError) => {
  // Process in batches to avoid overwhelming the model
  let taskBatches = Array.chunk(batchSize, tasks);

  List.IO.traverse(
    batch => {
      List.IO.traverse(
        task =>
          digestSingleTest(
            ~prompts,
            ~modelName,
            ~outputPath,
            ~promptIterations,
            task,
            (),
          ),
        Array.toList(batch),
      )
    },
    Array.toList(taskBatches),
  )
  |> IO.map(batchResults => {batchResults |> List.flatten |> Array.fromList});
};

/* Utility functions using shared implementations */
module DigestUtils = {
  let loadAndDigestJsonl =
      (
        ~modelName: string,
        ~inputPath: string,
        ~outputPath: string,
        ~promptIterations: int=1,
        (),
      ) // Number of times to run each prompt
      : IO.t(array(digestResult), string) => {
    // Use shared function to load evaluation dataset
    Shared.loadEvaluationDataset(inputPath)
    |> IO.tap(_ => Js.log("############ Loaded Data"))
    |> IO.flatMap(tasks => {
         digestMultipleTests(
           ~modelName,
           ~outputPath,
           ~promptIterations,
           tasks,
           (),
         )
         |> IO.mapError(error => {
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
            })
       });
  };

  let digestSingleTaskById =
      (
        ~modelName,
        ~inputPath: string,
        ~taskId: int,
        ~outputPath: string,
        ~promptIterations: int=1,
        (),
      ) // Number of times to run each prompt
      : IO.t(option(digestResult), string) => {
    // Use shared function to load evaluation dataset
    Shared.loadEvaluationDataset(inputPath)
    |> IO.tap(_ => Js.log("############ Loaded Data"))
    |> IO.flatMap(tasks => {
         // Use shared TaskUtils to find task by ID
         switch (Shared.TaskUtils.getTaskById(tasks, taskId)) {
         | Some(task) =>
           digestSingleTest(
             ~modelName,
             ~outputPath,
             ~promptIterations,
             task,
             (),
           )
           |> IO.map(result => Some(result))
           |> IO.mapError(error => {
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
              })
         | None => IO.pure(None)
         }
       });
  };

  /* Analysis functions for k-repeated prompts */
  let analyzePromptConsistency = (promptResult: promptResult): float => {
    // Calculate response consistency by comparing responses
    // For now, simple metric: ratio of unique responses to total responses
    let responses =
      Array.map(response => response.response, promptResult.responses);
    let uniqueResponses = String.Set.fromArray(responses) |> Set.length;
    Float.fromInt(uniqueResponses) /. Float.fromInt(Array.length(responses));
  };

  let getAverageResponseLength = (promptResult: promptResult): float => {
    let totalLength =
      Array.foldLeft(
        (acc, response) => acc + String.length(response.response),
        0,
        promptResult.responses,
      );
    Float.fromInt(totalLength)
    /. Float.fromInt(Array.length(promptResult.responses));
  };

  let getBestResponse =
      (promptResult: promptResult, ~scorer: string => float)
      : option(modelResponse) => {
    // Find the response with the highest score according to the scorer function
    Array.maxBy(
      (response1, response2) =>
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
