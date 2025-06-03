open Relude.Globals;

/**
 * Node.js File System bindings
 *
 * All external JavaScript bindings should be defined here with the following pattern:
 * 1. Raw external binding with a trailing apostrophe (e.g., readFileSync')
 * 2. IO-wrapped version without apostrophe for public use
 * 3. Group related bindings in modules (Fs, Path, etc.)
 */
module Fs = {
  // Raw external bindings
  // [@mel.module "fs"]
  // external readFileSync': (string, [@bs.string] [ | `utf8]) => string =
  //   "readFileSync";
  let readFileSync = (path, encoding) =>
    IO.triesJS(() => Node.Fs.readFileSync(path, encoding));
  // readFileSync'(path, encoding)

  [@mel.module "fs"]
  external readdir':
    (string, (Js.nullable(Js.Exn.t), array(string)) => unit) => unit =
    "readdir";

  [@mel.module "fs"]
  external stat': (string, (Js.nullable(Js.Exn.t), 'a) => unit) => unit =
    "stat";

  [@mel.module "fs"]
  external readdirSync': string => array(string) = "readdirSync";
  let readdirSync = path => IO.triesJS(() => readdirSync'(path));

  [@mel.module "fs"] external statSync': string => 'a = "statSync";
  let statSync = path => IO.triesJS(() => statSync'(path));

  /* Mkdir options type */
  type mkdirOptions = {. "recursive": bool};

  /* Create mkdir options object */
  let mkdirOptions = (~recursive: bool=false, ()) => {
    "recursive": recursive,
  };

  /* Raw external binding for mkdirSync */
  [@mel.module "fs"]
  external mkdirSync': (string, mkdirOptions) => unit = "mkdirSync";

  /* IO-wrapped version for public use */
  let mkdirSync = (path: string, options: mkdirOptions) =>
    IO.triesJS(() => mkdirSync'(path, options))
    |> IO.tapError(error => Js.log2("+++++++++++++++++++++", error));
};

/**
 * Node.js Path bindings
 */
module Path = {
  [@mel.module "path"] external join': (string, string) => string = "join";
  let join = (path1, path2) => IO.triesJS(() => join'(path1, path2));

  [@mel.module "path"] external normalize': string => string = "normalize";
  let normalize = path => IO.triesJS(() => normalize'(path));
};

/**
 * Node.js Process bindings
 */
module Process = {
  [@mel.module "process"] external cwd: unit => string = "cwd";

  /* Environment variables - raw external binding */
  // [@mel.module "process"] external env': 'a = "env";

  // /* Helper to get environment variable by name */
  // [@bs.get_index] external getEnvVar': ('a, string) => Js.nullable(string) = "";

  // /* IO-wrapped environment variable getter */
  // let getEnv = (varName: string): IO.t(option(string), Js.Exn.t) =>
  //   IO.triesJS(() => {
  //     let envObj = env';
  //     let nullableValue = getEnvVar'(envObj, varName);
  //     Js.Nullable.toOption(nullableValue);
  //   });

  [@mel.module "dotenv"] external getEnvVars: unit => unit = "config";

  // let getEnvVars = () =>
  //   getEnvVars()
  //   |> (() => Node.Process.process##env)
  //   |> (
  //     Js.Dict.map(~f=(. x) => x |> Utils.JsonUtils.Encode.string)
  //     >> Utils.JsonUtils.Encode.dict
  //   );
  let getEnvVars = () => getEnvVars() |> (() => Node.Process.process##env);

  /* Get environment variable with default value */
  let getEnvWithDefault = (varName: string, defaultValue: string): string =>
    getEnvVars() |> Js.Dict.get(_, varName) |> Option.getOrElse(defaultValue);

  let getEnvWithDefaultIO =
      (varName: string, defaultValue: string): IO.t(string, Js.Exn.t) =>
    getEnvVars()
    |> IO.pure
    |> IO.map(Js.Dict.get(_, varName) >> Option.getOrElse(defaultValue));
};

/**
 * Node.js stats object type
 */
type nodeStats = {
  [@bs.get]
  isDirectory: unit => bool,
  [@bs.get]
  isFile: unit => bool,
  [@bs.get]
  size: int,
};
