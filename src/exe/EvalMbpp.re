open Eval.Digest.DigestUtils;

let inputPath = "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/mbpp.jsonl";

let outputPath = "/Users/gb/github/ai-experiments/agent-architect/data/eval_output/test1.txt";

let taskId = 601;

Js.log("####### START #######");
let run = () => {
  Js.log("####### START #######");

  digestSingleTaskById(~modelName="", ~inputPath, ~taskId, ~outputPath)
  |> IO.tap(r => Js.log2("OUTPUT", r))
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(r) => Js.log2("####### OK #######", r)
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

run();
