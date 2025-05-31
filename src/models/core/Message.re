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
