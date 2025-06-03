open Eval.Digest.DigestUtils;

let inputPath = "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/mbpp.jsonl";

let outputPath = "/Users/gb/github/ai-experiments/agent-architect/data/eval_output/test1.json";

let taskId = 601;

let promptIterations = 2;

let run = () => {
  Js.log("####### START #######");

  digestSingleTaskById(
    ~modelName="",
    ~inputPath,
    ~taskId,
    ~outputPath,
    ~promptIterations,
    (),
  )
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_r) => Js.log("####### OK #######")
       | Error(err) => Js.log2("####### ERROR #######", err),
     );
};

run();
