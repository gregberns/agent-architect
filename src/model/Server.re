open Relude.Globals;
open Bindings.LangChain;

/**
 * Server.re - Modular abstractions for AI agent server architecture
 *
 * This module provides composable abstractions for building AI agent servers
 * with separate concerns for:
 * - Agent client management (LangGraph SDK)
 * - Thread persistence and retrieval
 * - Message processing and execution
 * - HTTP request handling
 */

///  Core types used across all modules
type userId = string;
type threadId = string;
type messageContent = string;
type assistantId = string;

type userMessage = {
  content: messageContent,
  userId,
  threadId: option(threadId),
};

type agentResponse = {
  content: messageContent,
  threadId,
  runId: string,
};

/// Agent client abstraction - manages LangGraph SDK client
module type AGENT_CLIENT = {
  type t;

  let create: (~deploymentUrl: string, ~assistantId: assistantId) => t;
  let getClient: t => client;
  let getAssistantId: t => assistantId;
};

/// Thread persistence abstraction - manages thread storage and retrieval
module type THREAD_STORE = {
  type t;

  let create: unit => IO.t(t, Js.Exn.t);
  let getThreadForUser: (t, userId) => IO.t(option(threadId), Js.Exn.t);
  let createThreadForUser: (t, userId) => IO.t(threadId, Js.Exn.t);
  let ensureThreadForUser: (t, userId) => IO.t(threadId, Js.Exn.t);
};

/// Message processor abstraction - handles message execution
module type MESSAGE_PROCESSOR = {
  type t;

  let create: (client, assistantId) => t;
  let processMessage:
    (
      ~threadId: threadId,
      ~content: messageContent,
      // ~multitaskStrategy: option(string)=?,
      t,
      unit
    ) =>
    IO.t(runResponse, Js.Exn.t);
  let waitForCompletion:
    (~threadId: threadId, ~runId: string, t) => IO.t(unit, Js.Exn.t);
};

/// HTTP request abstraction - handles incoming requests
module type REQUEST_HANDLER = {
  type request;
  type response;

  let extractUserMessage: request => IO.t(userMessage, Js.Exn.t);
  let sendResponse: (response, agentResponse) => IO.t(unit, Js.Exn.t);
  let sendError: (response, Js.Exn.t) => IO.t(unit, Js.Exn.t);
};

/// Main server functor that composes all abstractions
module Server =
       (
         AgentClient: AGENT_CLIENT,
         ThreadStore: THREAD_STORE,
         MessageProcessor: MESSAGE_PROCESSOR,
         RequestHandler: REQUEST_HANDLER,
       ) => {
  type serverState = {
    agentClient: AgentClient.t,
    threadStore: ThreadStore.t,
    messageProcessor: MessageProcessor.t,
  };

  let create =
      (~deploymentUrl: string, ~assistantId: assistantId)
      : IO.t(serverState, Js.Exn.t) => {
    let agentClient = AgentClient.create(~deploymentUrl, ~assistantId);
    let client = AgentClient.getClient(agentClient);
    let messageProcessor = MessageProcessor.create(client, assistantId);

    ThreadStore.create()
    |> IO.map(threadStore =>
         {
           agentClient,
           threadStore,
           messageProcessor,
         }
       );
  };

  let handleRequest =
      (
        serverState: serverState,
        request: RequestHandler.request,
        response: RequestHandler.response,
      )
      : IO.t(unit, Js.Exn.t) => {
    RequestHandler.extractUserMessage(request)
    |> IO.flatMap(({content, threadId, userId}) => {
         // Determine thread ID - use existing or create new
         let threadIdIO =
           switch (threadId) {
           | Some(threadId) => IO.pure(threadId)
           | None =>
             ThreadStore.ensureThreadForUser(serverState.threadStore, userId)
           };

         threadIdIO
         |> IO.flatMap(threadId => {
              // Process the message
              MessageProcessor.processMessage(
                serverState.messageProcessor,
                ~threadId,
                ~content,
                (),
              )
              |> IO.flatMap(runResponse => {
                   // Wait for completion
                   MessageProcessor.waitForCompletion(
                     ~threadId,
                     ~runId=runResponse.run_id,
                     serverState.messageProcessor,
                   )
                   |> IO.map(_ => {
                        {
                          // Create response (in real implementation, would get actual content from run)

                          content: "Agent response processed", // This would be actual agent response
                          threadId,
                          runId: runResponse.run_id,
                        }
                      })
                 })
              |> IO.flatMap(agentResponse => {
                   RequestHandler.sendResponse(response, agentResponse)
                 })
            });
       })
    |> IO.catchError(error => {RequestHandler.sendError(response, error)});
  };
};

// (** Concrete implementations *)

// (** Simple in-memory agent client *)
module InMemoryAgentClient: AGENT_CLIENT = {
  type t = {
    client,
    assistantId,
  };

  let create = (~deploymentUrl: string, ~assistantId: assistantId): t => {
    let client = createClient(~apiUrl=deploymentUrl);
    {
      client,
      assistantId,
    };
  };

  let getClient = (agentClient: t): client => agentClient.client;
  let getAssistantId = (agentClient: t): assistantId =>
    agentClient.assistantId;
};

// (** In-memory thread store *)
module InMemoryThreadStore: THREAD_STORE = {
  type t = {
    userThreads: Js.Dict.t(threadId),
    client,
  };

  let create = (): IO.t(t, Js.Exn.t) => {
    // Note: This requires a client for thread creation
    // In practice, this might be passed in or managed differently
    let client = createClient(~apiUrl="http://localhost:3002"); // Default for now
    IO.pure({
      userThreads: Js.Dict.empty(),
      client,
    });
  };

  let getThreadForUser =
      (store: t, userId: userId): IO.t(option(threadId), Js.Exn.t) => {
    let threadId = Js.Dict.get(store.userThreads, userId);
    IO.pure(threadId);
  };

  let createThreadForUser =
      (store: t, userId: userId): IO.t(threadId, Js.Exn.t) => {
    createThread(store.client)
    |> IO.map(threadResponse => {
         let threadId = threadResponse.thread_id;
         Js.Dict.set(store.userThreads, userId, threadId);
         threadId;
       });
  };

  let ensureThreadForUser =
      (store: t, userId: userId): IO.t(threadId, Js.Exn.t) => {
    getThreadForUser(store, userId)
    |> IO.flatMap(existingThread => {
         switch (existingThread) {
         | Some(threadId) => IO.pure(threadId)
         | None => createThreadForUser(store, userId)
         }
       });
  };
};

// (** Default message processor *)
module DefaultMessageProcessor: MESSAGE_PROCESSOR = {
  type t = {
    client,
    assistantId,
  };

  let create = (client: client, assistantId: assistantId): t => {
    {
      client,
      assistantId,
    };
  };

  let processMessage =
      (
        ~threadId: threadId,
        ~content: messageContent,
        // ~multitaskStrategy: option(string)=?,
        processor: t,
        (),
      )
      : IO.t(runResponse, Js.Exn.t) => {
    let messages = createMessages([(`Human, content)]);
    let input = createRunInput(messages);

    createRun(
      ~threadId,
      ~assistantId=processor.assistantId,
      ~input,
      // ~multitaskStrategy?,
      processor.client,
      (),
    );
  };

  let waitForCompletion =
      (~threadId: threadId, ~runId: string, processor: t)
      : IO.t(unit, Js.Exn.t) => {
    joinRun(~threadId, ~runId, processor.client);
  };
};

// // (** Express.js-like request handler (simplified for demonstration) *)
// module ExpressRequestHandler: REQUEST_HANDLER = {
//   type request = {
//     body: Js.Json.t,
//     headers: Js.Dict.t(string),
//   };

//   type response = {
//     send: Js.Json.t => unit,
//     status: int => unit,
//   };

//   let extractUserMessage = (request: request): IO.t(userMessage, Js.Exn.t) => {
//     IO.triesJS(() => {
//       // This would parse JSON body in real implementation
//       let userId = "default-user"; // Extract from auth/headers
//       let content = "Hello world"; // Extract from request.body
//       let threadId = None; // Extract from request if provided

//       {
//         userId,
//         content,
//         threadId,
//       };
//     });
//   };

//   let sendResponse =
//       (response: response, agentResponse: agentResponse)
//       : IO.t(unit, Js.Exn.t) => {
//     IO.triesJS(() => {
//       // Create JSON response
//       let jsonResponse =
//         Js.Json.object_(
//           Js.Dict.fromList([
//             ("content", Js.Json.string(agentResponse.content)),
//             ("threadId", Js.Json.string(agentResponse.threadId)),
//             ("runId", Js.Json.string(agentResponse.runId)),
//           ]),
//         );
//       response.send(jsonResponse);
//     });
//   };

//   let sendError = (response: response, error: Js.Exn.t): IO.t(unit, Js.Exn.t) => {
//     IO.triesJS(() => {
//       response.status(500);
//       let errorResponse =
//         Js.Json.object_(
//           Js.Dict.fromList([
//             ("error", Js.Json.string(Js.Exn.message(error))),
//           ]),
//         );
//       response.send(errorResponse);
//     });
//   };
// };

// // (** Composed server module *)
// module DefaultServer =
//   Server(
//     InMemoryAgentClient,
//     InMemoryThreadStore,
//     DefaultMessageProcessor,
//     ExpressRequestHandler,
//   );

// // (** Convenience functions for creating server instances *)
// let createDefaultServer =
//     (~deploymentUrl: string, ~assistantId: assistantId="agent", ())
//     : IO.t(DefaultServer.serverState, Js.Exn.t) => {
//   DefaultServer.create(~deploymentUrl, ~assistantId);
// };

// let handleExpressRequest =
//     (
//       serverState: DefaultServer.serverState,
//       request: ExpressRequestHandler.request,
//       response: ExpressRequestHandler.response,
//     )
//     : IO.t(unit, Js.Exn.t) => {
//   DefaultServer.handleRequest(serverState, request, response);
// };
