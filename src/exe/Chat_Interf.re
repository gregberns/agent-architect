module type DB = {
  let connect: unit => unit;
};

module App = (Database: DB) => {
  let run = () => Database.connect();
};

module PostgresDB: DB = {
  let connect = () => print_endline("Connecting to Postgres");
};

module MyApp = App(PostgresDB);

//
//
//
//

module Message = {
  type t = {
    role: string,
    content: string,
  };
  let make = (~role, content) => {
    role,
    content,
  };
  let makeSystem = content => make(~role="system", content);
  let makeAssistant = content => make(~role="assistant", content);
  let makeUser = content => make(~role="user", content);
};

module ModelInput = {
  type t = {messages: list(Message.t)};
  let make = messages => {messages: messages};
  let make1 = message => make([message]);
  let add = ({messages}, message) => make(List.append(message, messages));
};

module AIMessageChunk = {
  type t = {text: string};
};

module type MODEL = {
  type t;
  type err = Js.Exn.t;
  let make: unit => IO.t(t, err);
  let invoke: (t, ModelInput.t) => IO.t(AIMessageChunk.t, err);
};

module GeminiModel =
       (
         Config: {
           let model: string;
           let apiKey: string;
           let temperature: float;
         },
       )
       : MODEL => {
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
      ({role, content}: Message.t): Bindings.LangChain.messageObject => {
    role,
    content,
  };
  let mapResponse =
      ({content, _}: Bindings.LangChain.chatResponse): AIMessageChunk.t => {
    text: content,
  };

  let invoke = (model: t, {messages}: ModelInput.t) =>
    Bindings.LangChain.invokeWithMessageObjects(
      model,
      messages |> List.toArray |> Array.map(mapMessage),
    )
    |> IO.map(mapResponse);
};

module Chat = (Model: MODEL) => {
  let init = () => Model.make();
  let sendMessage = message => Model.invoke(message);
};

// Need a way to emit messages.
//  When in Console, should be write lines (with no delay)
//  When elsewhere, need to emit messages through a configurable module
//    that could say write to a web socket

//
//
//  Config
//

let googleApiKey =
  Bindings.NodeJs.Process.getEnvWithDefault("GEMINI_API_KEY", "NOT VALID");

module LoadedGeminiModel =
  GeminiModel({
    let model = "gemini-2.0-flash";
    let apiKey = googleApiKey;
    let temperature = 1.0;
  });

module MyChat = Chat(LoadedGeminiModel);

//
//
// Impl
//

let simpleStringChat = (): IO.t(unit, Js.Exn.t) => {
  let ( let* ) = IO.bind;
  Js.Console.log("=== Starting Simple String Chat ===");
  let model = MyChat.init();

  let history =
    "What is the capital of France? Please answer in one sentence."
    |> Message.makeUser
    |> ModelInput.make1;

  let* model = model;
  let* {text: response1} = MyChat.sendMessage(model, history);
  let history = ModelInput.add(history, response1 |> Message.makeAssistant);

  Js.log2("Model Response1:", response1);

  let prompt2 = "Using the answer, what is a prominent landmark in that location? Be concise.";

  let history = ModelInput.add(history, prompt2 |> Message.makeUser);

  let* {text: response2} = MyChat.sendMessage(model, history);

  Js.log2("Model Response2:", response2) |> IO.pure;
};

simpleStringChat() |> IO.unsafeRunAsync(_ => ());
