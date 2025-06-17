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

type chatResponse = {
  [@mel.as "content"]
  content: string,
  [@mel.as "role"]
  role: option(string),
  // text: string,
};

type model;

/* Provider-specific configuration types */
type providerConfig = {
  [@mel.as "baseURL"]
  baseUrl: string,
  [@mel.as "model"]
  model: string,
  [@mel.as "temperature"]
  temperature: option(Temperature.t),
  [@mel.as "apiKey"]
  apiKey: ApiKey.t,
};

module Raw = {
  [@mel.module "openai"] [@mel.new]
  external createModel: providerConfig => model = "OpenAI";

  [@mel.send]
  external invokeWithMessageObjects':
    (model, Js.Array.t(messageObject)) => Js.Promise.t(chatResponse) =
    "invoke";
};

let createModel =
    (
      ~baseUrl: string,
      ~model: string,
      ~apiKey: ApiKey.t,
      ~temperature: option(Temperature.t)=Some(0.0),
      (),
    )
    : model =>
  Raw.createModel({
    baseUrl,
    model,
    temperature,
    apiKey,
  });

let invokeWithMessageObjects =
    (model: model, messages: array(messageObject))
    : IO.t(chatResponse, Js.Exn.t) =>
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.invokeWithMessageObjects'(model, messages)
  );
