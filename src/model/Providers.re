module Google = {
  module Gemini =
         (
           Config: {
             let model: string;
             let apiKey: string;
             let temperature: float;
           },
         )
         : ModelTypes.Model.MODEL => {
    type t = Bindings.LangChain.model;
    type err = Js.Exn.t;

    let make = () => {
      let model =
        Bindings.LangChain.createGoogleModel(
          ~model=Config.model,
          ~apiKey=Config.apiKey,
          ~temperature=
            Config.temperature |> Bindings.LangChain.Temperature.make,
          (),
        );

      model |> IO.pure;
    };

    let mapMessage =
        ({role, content}: ModelTypes.Message.t)
        : Bindings.LangChain.messageObject => {
      role,
      content,
    };
    let mapResponse =
        ({content, _}: Bindings.LangChain.chatResponse)
        : ModelTypes.AIMessageChunk.t => {
      text: content,
    };

    let invoke = (model: t, {messages}: ModelTypes.ModelInput.t) =>
      Bindings.LangChain.invokeWithMessageObjects(
        model,
        messages |> List.toArray |> Array.map(mapMessage),
      )
      |> IO.map(mapResponse);
  };
};

module Mistral =
       (
         Config: {
           let model: string;
           let apiKey: string;
           let temperature: float;
         },
       )
       : ModelTypes.Model.MODEL => {
  type t = Bindings.LangChain.model;
  type err = Js.Exn.t;

  let make = () => {
    Bindings.LangChain.createMistralModel(
      ~model=Config.model,
      ~apiKey=Config.apiKey,
      ~temperature=
        Config.temperature
        |> Bindings.LangChain.Temperature.make
        |> Option.pure,
      (),
    )
    |> IO.pure;
  };

  let mapMessage =
      ({role, content}: ModelTypes.Message.t)
      : Bindings.LangChain.messageObject => {
    role,
    content,
  };

  let mapResponse =
      ({content, _}: Bindings.LangChain.chatResponse)
      : ModelTypes.AIMessageChunk.t => {
    text: content,
  };

  let invoke = (model: t, {messages}: ModelTypes.ModelInput.t) =>
    Bindings.LangChain.invokeWithMessageObjects(
      model,
      messages |> List.toArray |> Array.map(mapMessage),
    )
    |> IO.map(mapResponse);
};

module OpenRouter =
       (
         Config: {
           let model: string;
           let apiKey: string;
           let temperature: float;
         },
       )
       : ModelTypes.Model.MODEL => {
  type t = Bindings.OpenRouter.model;
  type err = Js.Exn.t;

  let baseUrl = "https://openrouter.ai/api/v1";

  let make = () =>
    Bindings.OpenRouter.createModel(
      ~baseUrl,
      // ~model=Config.model,
      ~apiKey=Config.apiKey,
      // ~temperature=
      //   Config.temperature
      //   |> Bindings.OpenRouter.Temperature.make
      //   |> Option.pure,
      (),
    )
    |> IO.pure;

  let mapMessage =
      ({role, content}: ModelTypes.Message.t)
      : Bindings.OpenRouter.messageObject => {
    role,
    content,
  };

  let mapResponse =
      ({choices, _}: Bindings.OpenRouter.chatResponse)
      : ModelTypes.AIMessageChunk.t => {
    text:
      choices
      |> Array.head
      |> Option.map(({message: {content, _}}: Bindings.OpenRouter.choice) =>
           content
         )
      |> Option.getOrElse(""),
  };

  let invoke = (model: t, {messages}: ModelTypes.ModelInput.t) =>
    Bindings.OpenRouter.invokeWithMessageObjects(
      ~modelName=Config.model,
      ~messages=messages |> List.toArray |> Array.map(mapMessage),
      ~temperature=
        Config.temperature
        |> Bindings.OpenRouter.Temperature.make
        |> Option.pure,
      model,
    )
    |> IO.map(mapResponse);
};
