module EmitMessage = {
  type t = {content: string};
};

module type SINK = {
  type t;
  let write: EmitMessage.t => IO.t(unit, 'e);
};

module type EMITTER = {
  let emitText: string => IO.t(unit, 'e);
  let emitMessage: EmitMessage.t => IO.t(unit, 'e);
};

module ConsoleSink: SINK = {
  type t;
  let write = message => Js.log(message) |> IO.pure;
};

module BasicEmitter = (Sink: SINK) : EMITTER => {
  let emitText = (message: string) => Sink.write({content: message});
  let emitMessage = (message: EmitMessage.t) => Sink.write(message);
};

module ConsoleEmitter = BasicEmitter(ConsoleSink);

//
//
//
//
//

module Chat = (Model: ModelTypes.Model.MODEL, Emit: EMITTER) => {
  let ( let* ) = IO.bind;

  let init = () => Model.make();

  let sendMessage = (model, message: ModelTypes.ModelInput.t) => {
    let* _ =
      Emit.emitText(
        message
        |> ModelTypes.ModelInput.last
        |> Option.map(ModelTypes.Message.toDisplayString)
        |> Option.getOrElse("<<No Last Message Found>>"),
      );

    Model.invoke(model, message)
    |> IO.flatMap(({text} as msg: ModelTypes.AIMessageChunk.t) =>
         Emit.emitText(text) |> IO.map(() => msg)
       );
  };
};

//
//
//  Config
//

let googleApiKey =
  Bindings.NodeJs.Process.getEnvWithDefault("GEMINI_API_KEY", "NOT VALID");

module LoadedGeminiModel =
  Model.Gemini.Model({
    let model = "gemini-2.0-flash";
    let apiKey = googleApiKey;
    let temperature = 1.0;
  });

module MyChat = Chat(LoadedGeminiModel, ConsoleEmitter);

//
//
// Impl
//

let simpleStringChat = (): IO.t(unit, Js.Exn.t) => {
  open ModelTypes;
  let ( let* ) = IO.bind;
  Js.Console.log("=== Starting Simple String Chat ===");
  let* model = MyChat.init();

  let history =
    "What is the capital of France? Please answer in one sentence."
    |> Message.makeUser
    |> ModelInput.make1;

  let* {text: response1} = MyChat.sendMessage(model, history);

  let history = ModelInput.add(history, response1 |> Message.makeAssistant);

  // Js.log2("Model Response1:", response1);

  let prompt2 = "Using the answer, what is a prominent landmark in that location? Be concise.";

  let history = ModelInput.add(history, prompt2 |> Message.makeUser);

  let* {text: _response2} = MyChat.sendMessage(model, history);

  // Js.log2("Model Response2:", response2) |> IO.pure;
  IO.pure();
};

simpleStringChat() |> IO.unsafeRunAsync(_ => ());
