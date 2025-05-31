type t = {
  content: string,
  role: string,
};

let make = (~role, content) => {
  content,
  role,
};

let makeSystem = content => make(~role="system", content);
let makeAssistant = content => make(~role="assistant", content);
let makeUser = content => make(~role="user", content);

let toDisplayString = ({content, role}) => {j|($role): $content|j};
