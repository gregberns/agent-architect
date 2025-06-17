open Relude.Globals;

module type CHAT = {
  type t;
  type err;
  let init: unit => IO.t(t, err);
  let sendMessage:
    (t, ModelTypes.ModelInput.t) => IO.t(ModelTypes.AIMessageChunk.t, err);
  let errorToString: err => option(string);
  // let getModelName: t => string;
};

module Chat = (Model: ModelTypes.Model.MODEL) => {
  type t = Model.t;
  type err = Js.Exn.t;
  let init = () => Model.make();

  let sendMessage = (model, message: ModelTypes.ModelInput.t) =>
    Model.invoke(model, message);

  let errorToString: err => option(string) = Js.Exn.message;
};
