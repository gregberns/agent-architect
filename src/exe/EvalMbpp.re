open Eval.Digest.DigestUtils;

type inputModel = {
  sourceDataPath: string,
  promptsPath: string,
};

let inputData = {
  sourceDataPath: "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/source-data/mbpp.jsonl",
  promptsPath: "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/prompt-runs/001_prompt.json",
};

type outputModel = {
  modelResponseOutputPath: string,
  compilePath: string,
  resultsPath: string,
};

let outputData = {
  modelResponseOutputPath: "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/outputs/runs/",
  compilePath: "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/outputs/scratch/",
  resultsPath: "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/outputs/results/",
};

let inputPath = "/Users/gb/github/ai-experiments/agent-architect/data/evaluation/inputs/source-data/mbpp.jsonl";
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
