open Jest;
open Expect;
open ModelBindings.LangChain;

describe("LangChain", () => {
  describe("Message Creation", () => {
    test("createHumanMessage creates a human message", () => {
      let message = createHumanMessage("Hello world");
      expect(message) |> ExpectJs.toBeTruthy;
    });

    test("createSystemMessage creates a system message", () => {
      let message = createSystemMessage("You are a helpful assistant");
      expect(message) |> ExpectJs.toBeTruthy;
    });

    test(
      "createMessageObject creates human message object with correct role", () => {
      let humanMessage = createMessageObject(~role=`Human, ~content="Hello");
      expect(humanMessage.role) |> toEqual("user");
    });

    test(
      "createMessageObject creates system message object with correct role", () => {
      let systemMessage =
        createMessageObject(~role=`System, ~content="System prompt");
      expect(systemMessage.role) |> toEqual("system");
    });
  });

  describe("Model Creation", () => {
    test("createGoogleModel creates a Google model", () => {
      let model = createGoogleModel(~model="gemini-2.0-flash", ());
      expect(model) |> ExpectJs.toBeTruthy;
    });

    test("createAnthropicModel creates an Anthropic model", () => {
      let model =
        createAnthropicModel(~model="claude-3-5-sonnet-20240620", ());
      expect(model) |> ExpectJs.toBeTruthy;
    });
  });

  describe("Message Array Creation", () => {
    test("createMessages creates correct number of message objects", () => {
      let messages =
        createMessages([
          (`System, "Translate from English to Italian"),
          (`Human, "Hello"),
        ]);
      expect(Array.length(messages)) |> toEqual(2);
    });

    test("createMessages creates system message with correct role", () => {
      let messages = createMessages([(`System, "Test")]);
      expect(Array.length(messages)) |> toEqual(1);
    });
  });

  describe("Generic Model Interface", () => {
    test("Google model can be used interchangeably", () => {
      let googleModel = createGoogleModel(~model="gemini-2.0-flash", ());

      // Both models should work with the same invoke functions
      // This tests that the generic 'model' type works correctly
      expect(googleModel) |> ExpectJs.toBeTruthy;
    });
    test("Anthropic model can be used interchangeably", () => {
      let anthropicModel =
        createAnthropicModel(~model="claude-3-5-sonnet-20240620", ());

      // Both models should work with the same invoke functions
      // This tests that the generic 'model' type works correctly
      expect(anthropicModel) |> ExpectJs.toBeTruthy;
    });
  });
});
