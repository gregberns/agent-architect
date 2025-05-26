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
  [@bs.module "fs"]
  external readFileSync': (string, [@bs.string] [ | `utf8]) => string =
    "readFileSync";
  let readFileSync = (path, encoding) =>
    IO.triesJS(() => readFileSync'(path, encoding));

  [@bs.module "fs"]
  external readdir':
    (string, (Js.nullable(Js.Exn.t), array(string)) => unit) => unit =
    "readdir";

  [@bs.module "fs"]
  external stat': (string, (Js.nullable(Js.Exn.t), 'a) => unit) => unit =
    "stat";

  [@bs.module "fs"]
  external readdirSync': string => array(string) = "readdirSync";
  let readdirSync = path => IO.triesJS(() => readdirSync'(path));

  [@bs.module "fs"] external statSync': string => 'a = "statSync";
  let statSync = path => IO.triesJS(() => statSync'(path));
};

/**
 * Node.js Path bindings
 */
module Path = {
  [@bs.module "path"] external join: (string, string) => string = "join";

  [@bs.module "path"] external normalize: string => string = "normalize";
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
