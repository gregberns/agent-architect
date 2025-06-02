module ConsoleSink: Emitter.SINK = {
  type t;

  // let prettyPrint:
  //   {
  //     .
  //     type_: string,
  //     content: string,
  //   } =>
  //   unit = [%mel.raw
  //   {|
  //   function prettyPrint(m) {
  //     const padded = " " + m['type'] + " ";
  //     const sepLen = Math.floor((80 - padded.length) / 2);
  //     const sep = "=".repeat(sepLen);
  //     const secondSep = sep + (padded.length % 2 ? "=" : "");

  //     console.log(`${sep}${padded}${secondSep}`);
  //     console.log("\n\n");
  //     console.log(m.content);
  //   }
  // |}
  // ];

  // let write: Emitter.EmitMessage.t => IO.t(unit, 'e) =
  // ({content}) =>
  //   prettyPrint({
  //     type_: "test",
  //     content,
  //   })
  //   |> IO.pure;
  let write = message => Js.log(message) |> IO.pure;
};

module ConsoleEmitter = Emitter.BasicEmitter(ConsoleSink);

//
//
//
//
//

module Chat = (Model: ModelTypes.Model.MODEL, Emit: Emitter.EMITTER) => {
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
  Bindings.NodeJs.Process.getEnvWithDefault("GOOGLE_API_KEY", "NOT VALID");

let gemini_2_0_flash = "gemini-2.0-flash";

module LoadedGeminiModel =
  Model.Gemini.Model({
    let model = gemini_2_0_flash;
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
