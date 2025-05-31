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
