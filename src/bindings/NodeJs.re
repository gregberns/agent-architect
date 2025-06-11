open Relude.Globals;

module Child_process = {
  /* Types from Node.js API */
  type execException;
  type childProcess;

  type execCallback = (Js.nullable(execException), string, string) => unit;

  [@mel.module "node:child_process"]
  external exec: (string, execCallback) => childProcess = "exec";

  let exec: string => IO.t(string, string) =
    cmd =>
      IO.async(onDone =>
        exec(
          cmd,
          (error: Js.nullable(execException), stdout: string, stderr: string) => {
          (
            switch (error |> Js.Nullable.toOption) {
            | Some(_e) => stderr |> Result.error
            | None => stdout |> Result.pure
            }
          )
          |> (res => onDone(res))
        })
        |> ignore
      );
};

/**
 * Node.js File System bindings
 *
 * All external JavaScript bindings should be defined here with the following pattern:
 * 1. Raw external binding with a trailing apostrophe (e.g., readFileSync')
 * 2. IO-wrapped version without apostrophe for public use
 * 3. Group related bindings in modules (Fs, Path, etc.)
 */
module Fs = {
  type fileFlags =
    | [@mel.as "r"] Read
    | [@mel.as "r+"] Read_write
    | [@mel.as "rs+"] Read_write_sync
    | [@mel.as "w"] Write
    | [@mel.as "wx"] Write_fail_if_exists
    | [@mel.as "w+"] Write_read
    | [@mel.as "wx+"] Write_read_fail_if_exists
    | [@mel.as "a"] Append
    | [@mel.as "ax"] Append_fail_if_exists
    | [@mel.as "a+"] Append_read
    | [@mel.as "ax+"] Append_read_fail_if_exists;

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

  type fileEncoding = [ | `utf8];

  type writeFileOptions = {
    encoding: Js.nullable(fileEncoding),
    flag: Js.nullable(fileFlags),
    mode: Js.nullable(int),
  };

  let makeWriteFileOptions =
      (~encoding=`utf8, ~flag=?, ~mode=?, ()): writeFileOptions => {
    encoding: encoding |> Js.Nullable.return,
    flag: flag |> Js.Nullable.fromOption,
    mode: mode |> Js.Nullable.fromOption,
  };

  [@mel.module "fs"]
  external writeFileSync: (string, string, writeFileOptions) => unit =
    "writeFileSync";

  [@mel.module "fs"]
  external writeFileAsUtf8Sync: (string, string, [@mel.as "utf8"] _) => unit =
    "writeFileSync";
  let writeFileAsUtf8Sync = (filename, content) =>
    IO.triesJS(() => writeFileAsUtf8Sync(filename, content));

  /* write to a file, if directories don't exist create them */
  let writeFileSyncRecursive: (string, string, writeFileOptions) => unit = [%mel.raw
    {|function writeFileSyncRecursive(filename, content, charset) {
        const fs = require('fs');

        // -- normalize path separator to '/' instead of path.sep,
        // -- as / works in node for Windows as well, and mixed \\ and / can appear in the path
        let filepath = filename.replace(/\\/g,'/');

        // -- preparation to allow absolute paths as well
        let root = '';
        if (filepath[0] === '/') {
          root = '/';
          filepath = filepath.slice(1);
        }
        else if (filepath[1] === ':') {
          root = filepath.slice(0,3);   // c:\
          filepath = filepath.slice(3);
        }

        // -- create folders all the way down
        const folders = filepath.split('/').slice(0, -1);  // remove last item, file
        folders.reduce(
          (acc, folder) => {
            const folderPath = acc + folder + '/';
            if (!fs.existsSync(folderPath)) {
              fs.mkdirSync(folderPath);
            }
            return folderPath
          },
          root // first 'acc', important
        );

        // -- write file
        fs.writeFileSync(root + filepath, content, charset);
      }
    |}
  ];
  let writeFileSyncRecursive = (filename, content, options) =>
    IO.triesJS(() => writeFileSyncRecursive(filename, content, options));

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

/**
 * Sleep utility
 */
module Sleep = {
  /* Raw setTimeout binding */
  [@mel.scope "global"] 
  external setTimeout: (unit => unit, int) => 'timeoutId = "setTimeout";

  /* Sleep function wrapped in IO that takes milliseconds */
  let sleep = (milliseconds: int): IO.t(unit, 'e) =>
    IO.async(onDone =>
      setTimeout(() => onDone(Result.Ok()), milliseconds) |> ignore
    );
};
