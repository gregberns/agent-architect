module AIMessageChunk = {
  type t = {
    role: string,
    content: string,
  };
};

module ModelInput = {
  type t = {messages: list(string)};
};

module type MODEL = {
  type t = {provider: string};
};

module type AGENT =
  (M: MODEL) =>
   {
    type t;
    let invoke: (M.t, ModelInput.t) => IO.t(AIMessageChunk.t, string);
  };
