module Model =
       (
         Config: {
           let model: string;
           let apiKey: string;
           let temperature: float;
         },
       )
       : ModelTypes.Model.MODEL => {
  type t = ModelBindings.LangChain.model;
  type err = Js.Exn.t;

  let make = () => {
    let model =
      ModelBindings.LangChain.createGoogleModel(
        ~model=Config.model,
        ~apiKey=Config.apiKey,
        ~temperature=
          Config.temperature |> ModelBindings.LangChain.Temperature.make,
        (),
      );

    model |> IO.pure;
  };

  let mapMessage =
      ({role, content}: ModelTypes.Message.t)
      : ModelBindings.LangChain.messageObject => {
    role,
    content,
  };
  let mapResponse =
      ({content, _}: ModelBindings.LangChain.chatResponse)
      : ModelTypes.AIMessageChunk.t => {
    text: content,
  };

  let invoke = (model: t, {messages}: ModelTypes.ModelInput.t) =>
    ModelBindings.LangChain.invokeWithMessageObjects(
      model,
      messages |> List.toArray |> Array.map(mapMessage),
    )
    |> IO.map(mapResponse);
};
