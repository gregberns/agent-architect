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

module BasicEmitter = (Sink: SINK) : EMITTER => {
  let emitText = (message: string) => Sink.write({content: message});
  let emitMessage = (message: EmitMessage.t) => Sink.write(message);
};
