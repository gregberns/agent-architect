open Relude.Globals;
open Bindings.LangChain;

/**
 * Server.re - ReasonML implementation of LangGraph SDK usage
 *
 * This mirrors the JavaScript example:
 *
 * import { Client } from "@langchain/langgraph-sdk";
 * const client = new Client({ apiUrl: <DEPLOYMENT_URL> });
 * const assistantId = "agent";
 * const thread = await client.threads.create();
 *
 * let interruptedRun = await client.runs.create(
 *   thread["thread_id"],
 *   assistantId,
 *   { input: { messages: [{ role: "human", content: "what's the weather in sf?" }] } }
 * );
 *
 * let run = await client.runs.create(
 *   thread["thread_id"],
 *   assistantId,
 *   {
 *     input: { messages: [{ role: "human", content: "what's the weather in nyc?" }] },
 *     multitaskStrategy: "interrupt"
 *   }
 * );
 *
 * await client.runs.join(thread["thread_id"], run["run_id"]);
 */

type serverConfig = {
  deploymentUrl: string,
  assistantId: string,
};

let createServerExample =
    (~deploymentUrl: string, ~assistantId: string="agent", ()) => {
  let client = createClient(~apiUrl=deploymentUrl);

  let runExample = (): IO.t(unit, Js.Exn.t) => {
    createThread(client)
    |> IO.flatMap(threadResponse => {
         let threadId = threadResponse.thread_id;

         // First run - will be interrupted
         let firstMessages =
           createMessages([(`Human, "what's the weather in sf?")]);
         let firstInput = createRunInput(firstMessages);

         createRun(client, ~threadId, ~assistantId, ~input=firstInput, ())
         |> IO.flatMap(_interruptedRun => {
              // Second run with multitask strategy
              let secondMessages =
                createMessages([(`Human, "what's the weather in nyc?")]);
              let secondInput = createRunInput(secondMessages);

              createRun(
                client,
                ~threadId,
                ~assistantId,
                ~input=secondInput,
                ~multitaskStrategy="interrupt",
                (),
              )
              |> IO.flatMap(run => {
                   // Wait for the second run to complete
                   joinRun(
                     client,
                     ~threadId,
                     ~runId=run.run_id,
                   )
                 });
            });
       });
  };

  runExample;
};

// Example usage function
let runServerExample = (deploymentUrl: string): IO.t(unit, Js.Exn.t) => {
  let exampleRunner = createServerExample(~deploymentUrl, ());
  exampleRunner();
};

// Convenience function for testing with a specific deployment URL
let runWithTestUrl = (): IO.t(unit, Js.Exn.t) => {
  // Replace with actual deployment URL when available
  let testUrl = "http://localhost:3002";
  runServerExample(testUrl);
};
