open Relude.Globals;

/**
 * LangChain bindings for Melange/ReasonML
 * Provides type-safe access to LangChain JavaScript library
 *
 * Following the pattern from NodeJs.re:
 * 1. Raw external bindings with apostrophe suffix
 * 2. IO-wrapped versions for public use
 * 3. All effects wrapped in IO monad
 */

/* Message types */
type messageRole = [
  | `System
  | `Human
  | `Assistant
];

type messageObject = {
  [@mel.as "role"]
  role: string,
  [@mel.as "content"]
  content: string,
};

type humanMessage;
type systemMessage;
type assistantMessage;

/* API Key module */
module ApiKey = {
  type t = string;
};

/* Temperature module */
module Temperature = {
  type t = float;
  let make: float => t = id;
};

/* Generic model type that works with any LangChain chat model */
type model;

/* Provider-specific configuration types */
type googleConfig = {
  [@mel.as "model"]
  model: string,
  [@mel.as "temperature"]
  temperature: option(Temperature.t),
  [@mel.as "apiKey"]
  apiKey: ApiKey.t,
};

type anthropicConfig = {
  [@mel.as "model"]
  model: string,
  [@mel.as "temperature"]
  temperature: Temperature.t,
  [@mel.as "anthropicApiKey"]
  anthropicApiKey: ApiKey.t,
};

/* Response type */
type chatResponse = {
  [@mel.as "content"]
  content: string,
  [@mel.as "role"]
  role: option(string),
  // text: string,
};

/* LangGraph SDK types */
type clientConfig = {
  [@mel.as "apiUrl"]
  apiUrl: string,
};

type client;
type thread;
type run;

type threadResponse = {
  [@mel.as "thread_id"]
  thread_id: string,
};

type runResponse = {
  [@mel.as "run_id"]
  run_id: string,
};

type runInput = {
  [@mel.as "messages"]
  messages: array(messageObject),
};

type runConfig = {
  [@mel.as "input"]
  input: runInput,
  [@mel.as "multitaskStrategy"]
  multitaskStrategy: option(string),
};

/* Raw bindings - all with apostrophe suffix */
module Raw = {
  /* Message constructors - these are pure, no apostrophe needed */
  [@mel.module "@langchain/core/messages"] [@mel.new]
  external createHumanMessage: string => humanMessage = "HumanMessage";

  [@mel.module "@langchain/core/messages"] [@mel.new]
  external createSystemMessage: string => systemMessage = "SystemMessage";

  /* Model constructors - these are pure, no apostrophe needed */
  [@mel.module "@langchain/google-genai"] [@mel.new]
  external createChatGoogleGenerativeAI: googleConfig => model =
    "ChatGoogleGenerativeAI";

  [@mel.module "@langchain/anthropic"] [@mel.new]
  external createChatAnthropic: anthropicConfig => model = "ChatAnthropic";

  /* Invoke methods - these are effectful, need apostrophe suffix */
  [@mel.send]
  external invokeWithString': (model, string) => Js.Promise.t(chatResponse) =
    "invoke";

  [@mel.send]
  external invokeWithMessages':
    (model, Js.Array.t('a)) => Js.Promise.t(chatResponse) =
    "invoke";

  [@mel.send]
  external invokeWithMessageObjects':
    (model, Js.Array.t(messageObject)) => Js.Promise.t(chatResponse) =
    "invoke";

  /* LangGraph SDK Client bindings */
  [@mel.module "@langchain/langgraph-sdk"] [@mel.new]
  external createClient: clientConfig => client = "Client";

  [@mel.get] external threads: client => 'a = "threads";
  [@mel.get] external runs: client => 'a = "runs";

  [@mel.send]
  external createThread': 'a => Js.Promise.t(threadResponse) = "create";

  [@mel.send]
  external createRun':
    ('a, string, string, runConfig) => Js.Promise.t(runResponse) =
    "create";

  [@mel.send]
  external joinRun': ('a, string, string) => Js.Promise.t(unit) = "join";
};

/* Public API */

/* Message constructors - pure functions, no IO needed */
let createHumanMessage = (content: string): humanMessage =>
  Raw.createHumanMessage(content);

let createSystemMessage = (content: string): systemMessage =>
  Raw.createSystemMessage(content);

/* Model constructors - pure functions, no IO needed */
let createGoogleModel =
    (
      ~model: string,
      ~apiKey: ApiKey.t,
      ~temperature: option(Temperature.t)=?,
      (),
    )
    : model =>
  Raw.createChatGoogleGenerativeAI({
    model,
    temperature,
    apiKey,
  });

let createAnthropicModel =
    (
      ~model: string,
      ~anthropicApiKey: ApiKey.t,
      ~temperature: Temperature.t=0.0,
      (),
    )
    : model =>
  Raw.createChatAnthropic({
    model,
    temperature,
    anthropicApiKey,
  });

/* Invoke methods - effectful operations wrapped in IO */
let invokeWithString =
    (model: model, prompt: string): IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.invokeWithString'(model, prompt)
  );

let invokeWithHumanMessages =
    (model: model, messages: array(humanMessage))
    : IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.invokeWithMessages'(model, messages)
  );

let invokeWithSystemMessages =
    (model: model, messages: array(systemMessage))
    : IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.invokeWithMessages'(model, messages)
  );

let invokeWithMessageObjects =
    (model: model, messages: array(messageObject))
    : IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.invokeWithMessageObjects'(model, messages)
  );

/* LangGraph SDK Client functions - effectful operations wrapped in IO */
let createClient = (~apiUrl: string): client =>
  Raw.createClient({apiUrl: apiUrl});

let createThread = (client: client): IO.t(threadResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.createThread'(Raw.threads(client))
  );

let createRun =
    (
      client: client,
      ~threadId: string,
      ~assistantId: string,
      ~input: runInput,
      ~multitaskStrategy: option(string)=?,
      (),
    )
    : IO.t(runResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.createRun'(
      Raw.runs(client),
      threadId,
      assistantId,
      {
        input,
        multitaskStrategy,
      },
    )
  );

let joinRun =
    (client: client, ~threadId: string, ~runId: string): IO.t(unit, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.joinRun'(Raw.runs(client), threadId, runId)
  );

/* Convenience function for creating message objects - pure function */
let createMessageObject =
    (~role: messageRole, ~content: string): messageObject => {
  let roleString =
    switch (role) {
    | `System => "system"
    | `Human => "user"
    | `Assistant => "assistant"
    };
  {
    role: roleString,
    content,
  };
};

/* Helper to create arrays of messages - pure function */
let createMessages =
    (messages: list((messageRole, string))): array(messageObject) =>
  List.toArray(
    List.map(
      ((role, content)) => createMessageObject(~role, ~content),
      messages,
    ),
  );

/* Helper to create run input - pure function */
let createRunInput = (messages: array(messageObject)): runInput => {
  messages: messages,
};
