open Relude.Globals;
open Bindings.NodeJs;

/**
 * Digest.re - Process evaluation tests through model inference
 *
 * Workflow:
 * 1. Read in a single test
 * 2. Map over prompt list
 * 3. Traverse over (send to Model)
 * 4. Encode test + response
 * 5. Write output to file
 */

/* Types for digest processing */
type promptTemplate = {
  name: string,
  template: string,
  instructions: option(string),
};

type modelResponse = {
  prompt: string,
  response: string,
  model_name: string,
  timestamp: float,
};

type digestResult = {
  task: Ingest.evaluationTask,
  responses: array(modelResponse),
  processing_time: float,
};

type digestError = [
  | `ModelInvokeError(string)
  | `FileWriteError(Js.Exn.t)
  | `PromptGenerationError(string)
  | `EncodingError(string)
];

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

/* Stub model invoke function - to be replaced with actual model implementation */
let invokeModel =
    (~prompt: string, ~modelName as _: string): IO.t(string, string) => {
  MyChat.init()
  |> IO.flatMap(
       MyChat.sendMessage(
         _,
         ModelTypes.ModelInput.make1(ModelTypes.Message.makeUser(prompt)),
       ),
     )
  |> IO.map(({text}: ModelTypes.AIMessageChunk.t) => text)
  |> IO.mapError(
       Js.Exn.message
       >> Option.getOrElse("<<MODEL INVOKE ERROR - NO MESSAGE>>"),
     );
};

/* Default prompt templates for code evaluation */
module PromptTemplates = {
  let basicCodeGeneration: promptTemplate = {
    name: "basic_code_generation",
    template: "Problem: {text}\n\nGenerate ReasonML code to solve this problem:",
    instructions:
      Some(
        "Generate clean, working ReasonML code that solves the given problem.",
      ),
  };

  let codeWithTests: promptTemplate = {
    name: "code_with_tests",
    template: "Problem: {text}\n\nGenerate ReasonML code that passes these tests:\n{tests}\n\nCode:",
    instructions:
      Some("Generate ReasonML code that passes all the provided test cases."),
  };

  let codeExplanation: promptTemplate = {
    name: "code_explanation",
    template: "Problem: {text}\n\nExplain how to solve this problem step by step, then provide ReasonML code:",
    instructions:
      Some("First explain the approach, then provide working code."),
  };

  let codeOptimization: promptTemplate = {
    name: "code_optimization",
    template: "Problem: {text}\n\nProvide an optimized ReasonML solution with time/space complexity analysis:",
    instructions:
      Some("Focus on efficiency and provide complexity analysis."),
  };

  let defaultTemplates: array(promptTemplate) = [|
    basicCodeGeneration,
    codeWithTests,
    codeExplanation,
    codeOptimization,
  |];
};

/* Generate prompt from template and task */
let generatePrompt =
    (template: promptTemplate, task: Ingest.evaluationTask)
    : Result.t(string, string) => {
  let templateStr = template.template;

  // Replace {text} placeholder
  let withText =
    String.replaceEach(~search="{text}", ~replaceWith=task.text, templateStr);

  // Replace {tests} placeholder if present
  let testsStr = Array.String.intercalate("\n", task.test_list);
  let withTests =
    String.replaceEach(~search="{tests}", ~replaceWith=testsStr, withText);

  // Replace {code} placeholder if present (for reference)
  let withCode =
    String.replaceEach(~search="{code}", ~replaceWith=task.code, withTests);

  Result.Ok(withCode);
};

/* Process single test with one prompt template */
let processTestWithPrompt =
    (task: Ingest.evaluationTask, template: promptTemplate, modelName: string)
    : IO.t(modelResponse, digestError) => {
  // let startTime = Js.Date.now();
  switch (generatePrompt(template, task)) {
  | Result.Ok(prompt) =>
    invokeModel(~prompt, ~modelName)
    |> IO.mapError(error => `ModelInvokeError(error))
    |> IO.map(response => {
         {
           prompt,
           response,
           model_name: modelName,
           timestamp: Js.Date.now(),
         }
       })
  | Result.Error(error) => IO.throw(`PromptGenerationError(error))
  };
};

/* Process single test with multiple prompt templates */
let processSingleTest =
    (
      task: Ingest.evaluationTask,
      prompts: array(promptTemplate),
      modelName: string,
    )
    : IO.t(digestResult, digestError) => {
  let startTime = Js.Date.now();

  // Map over prompt list and traverse over IO operations
  List.IO.traverse(
    template => processTestWithPrompt(task, template, modelName),
    Array.toList(prompts),
  )
  |> IO.map(responseList => {
       let responses = Array.fromList(responseList);
       let processingTime = Js.Date.now() -. startTime;

       {
         task,
         responses,
         processing_time: processingTime,
       };
     });
};

/* Encode digest result to JSON */
module EncodeDigest = {
  // open Utils.JsonUtils;

  let encodeModelResponse = (response: modelResponse): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("prompt", Js.Json.string(response.prompt)),
        ("response", Js.Json.string(response.response)),
        ("model_name", Js.Json.string(response.model_name)),
        ("timestamp", Js.Json.number(response.timestamp)),
      ]),
    );
  };

  let encodeEvaluationTask = (task: Ingest.evaluationTask): Js.Json.t => {
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

  let encodeDigestResult = (result: digestResult): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task", encodeEvaluationTask(result.task)),
        (
          "responses",
          Js.Json.array(Array.map(encodeModelResponse, result.responses)),
        ),
        ("processing_time", Js.Json.number(result.processing_time)),
        ("processed_at", Js.Json.number(Js.Date.now())),
      ]),
    );
  };
};

/* Write digest result to file */
let writeDigestResult =
    (result: digestResult, outputPath: string): IO.t(unit, digestError) => {
  let jsonContent = EncodeDigest.encodeDigestResult(result);
  let jsonString = Js.Json.stringify(jsonContent);

  Fs.readFileSync(outputPath, `utf8)
  |> IO.catchError(_ => IO.pure(""))  // File doesn't exist, start with empty
  |> IO.flatMap(existingContent => {
       // Append to JSONL format
       let newLine =
         if (String.trim(existingContent) == "") {
           jsonString;
         } else {
           existingContent ++ "\n" ++ jsonString;
         };

       // Write back to file
       IO.triesJS(() => {Node.Fs.writeFileAsUtf8Sync(outputPath, newLine)})
       |> IO.mapError(error => `FileWriteError(error));
     });
};

/* Main digest processing function */
let digestSingleTest =
    (
      ~prompts: array(promptTemplate)=PromptTemplates.defaultTemplates,
      ~modelName: string,
      ~outputPath: string,
      task: Ingest.evaluationTask,
      (),
    )
    : IO.t(digestResult, digestError) => {
  processSingleTest(task, prompts, modelName)
  |> IO.flatMap(result => {
       writeDigestResult(result, outputPath) |> IO.map(_ => result)
     });
};

/* Batch processing functions */
let digestMultipleTests =
    (
      ~prompts: array(promptTemplate)=PromptTemplates.defaultTemplates,
      ~modelName: string,
      ~outputPath: string,
      ~batchSize: int=5,
      tasks: array(Ingest.evaluationTask),
      (),
    )
    : IO.t(array(digestResult), digestError) => {
  // Process in batches to avoid overwhelming the model
  let taskBatches = Array.chunk(batchSize, tasks);

  List.IO.traverse(
    batch => {
      List.IO.traverse(
        task => digestSingleTest(~prompts, ~modelName, ~outputPath, task, ()),
        Array.toList(batch),
      )
    },
    Array.toList(taskBatches),
  )
  |> IO.map(batchResults => {batchResults |> List.flatten |> Array.fromList});
};

/* Utility functions */
module DigestUtils = {
  let loadAndDigestJsonl =
      (~modelName: string, ~inputPath: string, ~outputPath: string)
      : IO.t(array(digestResult), string) => {
    Ingest.loadEvaluationDataset(inputPath)
    |> IO.flatMap(tasks => {
         digestMultipleTests(~modelName, ~outputPath, tasks, ())
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
      (~modelName, ~inputPath: string, ~taskId: int, ~outputPath: string)
      : IO.t(option(digestResult), string) => {
    Ingest.loadEvaluationDataset(inputPath)
    |> IO.flatMap(tasks => {
         switch (Ingest.TaskUtils.getTaskById(tasks, taskId)) {
         | Some(task) =>
           digestSingleTest(~modelName, ~outputPath, task, ())
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
};
