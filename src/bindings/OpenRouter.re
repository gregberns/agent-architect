module ApiKey = {
  type t = string;
};

/* Temperature module */
module Temperature = {
  type t = float;
  let make: float => t = id;
};

type messageObject = {
  [@mel.as "role"]
  role: string,
  [@mel.as "content"]
  content: string,
};

type message = {
  [@mel.as "content"]
  content: string,
  [@mel.as "role"]
  role: string,
};

type choice = {
  [@mel.as "message"]
  message,
};

type chatResponse = {
  [@mel.as "choices"]
  choices: array(choice),
};

type model;

/* Provider-specific configuration types */
type providerConfig = {
  [@mel.as "baseURL"]
  baseUrl: string,
  [@mel.as "apiKey"]
  apiKey: ApiKey.t,
  [@mel.as "defaultHeaders"]
  defaultHeaders: option(Js.Dict.t(string)),
};

type completionRequest = {
  [@mel.as "model"]
  model: string,
  [@mel.as "messages"]
  messages: array(messageObject),
  [@mel.as "temperature"]
  temperature: option(Temperature.t),
};

module Raw = {
  [@mel.module "openai"] [@mel.new]
  external createModel: providerConfig => model = "OpenAI";

  [@mel.get] external chat: model => 'a = "chat";

  [@mel.get] external completions: 'a => 'b = "completions";

  [@mel.send]
  external create: ('b, completionRequest) => Js.Promise.t(chatResponse) =
    "create";
};

let createModel =
    (
      ~baseUrl: string,
      ~apiKey: ApiKey.t,
      ~defaultHeaders: option(Js.Dict.t(string))=None,
      (),
    )
    : model =>
  Raw.createModel({
    baseUrl,
    apiKey,
    defaultHeaders,
  });

let invokeWithMessageObjects =
    (
      ~modelName: string,
      ~messages: array(messageObject),
      ~temperature: option(Temperature.t)=Some(0.0),
      model: model,
    )
    : IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.create(
      Raw.completions(Raw.chat(model)),
      {
        model: modelName,
        messages,
        temperature,
      },
    )
  );
