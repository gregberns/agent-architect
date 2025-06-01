module Model =
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
        ~temperature=Config.temperature |> Bindings.LangChain.Temperature.make,
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
