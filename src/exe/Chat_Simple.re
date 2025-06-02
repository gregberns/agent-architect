open Relude.Globals;
// open Bindings.LangChain;

/**
 * Simple Chat Application
 * Demonstrates usage of LangChain bindings with Google Gemini
 */

/* Helper function to create API key */
let googleApiKey =
  Bindings.NodeJs.Process.getEnvWithDefault("GOOGLE_API_KEY", "NOT VALID");

/* Helper function to print chat responses */
let printResponse =
    (label: string, response: Bindings.LangChain.chatResponse): unit => {
  Js.Console.log("\n=== " ++ label ++ " ===");
  Js.Console.log("Content: " ++ response.content);
  switch (response.role) {
  | Some(role) => Js.Console.log("Role: " ++ role)
  | None => ()
  };
};

/* Simple string-based chat */
let simpleStringChat = (): IO.t(unit, Js.Exn.t) => {
  Js.Console.log("=== Starting Simple String Chat ===");

  let googleModel =
    Bindings.LangChain.createGoogleModel(
      ~model="gemini-2.0-flash",
      ~apiKey=googleApiKey,
      (),
    );

  let prompt = "What is the capital of France? Please answer in one sentence.";

  Bindings.LangChain.invokeWithString(googleModel, prompt)
  |> IO.map(googleResponse => {
       printResponse("Google Gemini Response", googleResponse)
     });
};

/* Message-based chat with conversation */
let conversationChat = (): IO.t(unit, Js.Exn.t) => {
  Js.Console.log("\n=== Starting Conversation Chat ===");

  let model =
    Bindings.LangChain.createGoogleModel(
      ~model="gemini-2.0-flash",
      ~apiKey=googleApiKey,
      (),
    );

  let userMessage =
    Bindings.LangChain.createHumanMessage(
      "Explain quantum computing in simple terms.",
    );

  Bindings.LangChain.invokeWithHumanMessages(model, [|userMessage|])
  |> IO.flatMap(response1 => {
       printResponse("First Response", response1);

       /* Follow-up question */
       let followUpMessage =
         Bindings.LangChain.createHumanMessage(
           "Can you give me a practical example?",
         );
       Bindings.LangChain.invokeWithHumanMessages(
         model,
         [|followUpMessage|],
       );
     })
  |> IO.map(response2 => {printResponse("Follow-up Response", response2)});
};

/* Message objects chat */
let messageObjectsChat = (): IO.t(unit, Js.Exn.t) => {
  Js.Console.log("\n=== Starting Message Objects Chat ===");

  let model =
    Bindings.LangChain.createGoogleModel(
      ~model="gemini-2.0-flash",
      ~apiKey=googleApiKey,
      (),
    );

  let messages =
    Bindings.LangChain.createMessages([
      (`System, "You are a creative writer. Write in a poetic style."),
      (`Human, "Describe a sunset over the ocean."),
    ]);

  Bindings.LangChain.invokeWithMessageObjects(model, messages)
  |> IO.map(response => {printResponse("Creative Response", response)});
};

/* Error handling helper */
let handleError = (error: Js.Exn.t): unit => {
  Js.Console.error("Error occurred:");
  Js.Console.error(
    Js.Exn.message(error) |> Option.getOrElse("Unknown error"),
  );
};

/* Main chat application */
let runChatApp = (): unit => {
  Js.Console.log(
    "🚀 Starting LangChain Chat Application with Google Gemini",
  );
  Js.Console.log("Note: Make sure to set your Google API key!");

  /* Run all chat examples in sequence */
  simpleStringChat()
  |> IO.flatMap(_ => conversationChat())
  |> IO.flatMap(_ => messageObjectsChat())
  |> IO.bimap(
       _ => Js.Console.log("\n✅ Chat application completed successfully!"),
       handleError,
     )
  |> IO.unsafeRunAsync(_ => ());
};

/* Export for use in other modules */
// let run = runChatApp;
runChatApp();
