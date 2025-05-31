module type MODEL = {
  type t;
  type err = Js.Exn.t;
  let make: unit => IO.t(t, err);
  let invoke: (t, ModelInput.t) => IO.t(AIMessageChunk.t, err) /* }*/;
};
