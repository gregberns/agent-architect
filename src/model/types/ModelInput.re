type t = {messages: list(Message.t)};

let make = messages => {messages: messages};
let make1 = message => make([message]);
let add = ({messages}, message) => make(List.append(message, messages));
let last = ({messages}) => messages |> List.last;
