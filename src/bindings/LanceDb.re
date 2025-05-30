open Relude.Globals;

/**
 * LanceDB bindings for Melange/ReasonML
 * Provides type-safe access to LanceDB JavaScript client
 */

type t_database;
type t_table;

/* Configuration and data types */
type vector = array(float);

type record = {
  [@mel.as "vector"]
  vector,
  [@mel.as "text"]
  text: string,
  [@mel.as "id"]
  id: int,
};

type createTableOptions = {
  [@mel.as "writeMode"]
  writeMode: string,
};

type searchQuery = {
  vector,
  limit: option(int),
  select: option(array(string)),
  where: option(string),
};

type searchResult = {
  [@mel.as "text"]
  text: string,
  [@mel.as "id"]
  id: int,
  [@mel.as "_distance"]
  distance: option(float),
};

/* External bindings to LanceDB JavaScript client */
module Raw = {
  /* Database connection */
  [@mel.module "vectordb"]
  external connect': string => Js.Promise.t(t_database) = "connect";

  /* Table operations */
  [@mel.send]
  external createTable':
    (t_database, string, array(record), createTableOptions) =>
    Js.Promise.t(t_table) =
    "createTable";

  [@mel.send]
  external openTable': (t_database, string) => Js.Promise.t(t_table) =
    "openTable";

  [@mel.send]
  external add': (t_table, array(record)) => Js.Promise.t(unit) = "add";

  /* Search operations - using builder pattern */
  type t_searchBuilder;

  [@mel.send]
  external search': (t_table, vector) => t_searchBuilder = "search";

  [@mel.send]
  external limit': (t_searchBuilder, int) => t_searchBuilder = "limit";

  [@mel.send]
  external select': (t_searchBuilder, array(string)) => t_searchBuilder =
    "select";

  [@mel.send]
  external where': (t_searchBuilder, string) => t_searchBuilder = "where";

  [@mel.send]
  external execute': t_searchBuilder => Js.Promise.t(array(searchResult)) =
    "execute";
};

/* ReasonML-friendly wrapper types */
type database = {
  db: t_database,
  path: string,
};

type table = {
  table: t_table,
  name: string,
};

type recordData = {
  vector: list(float),
  text: string,
  id: int,
};

type searchOptions = {
  limit: option(int),
  select: option(list(string)),
  where: option(string),
};

type searchResults = list(searchResult);

/* Helper functions */
let recordDataToJs = ({vector, text, id, _}: recordData): record => {
  vector: Array.fromList(vector),
  text,
  id,
};

let searchOptionsToBuilder =
    (builder: Raw.t_searchBuilder, {limit, select, where, _}: searchOptions)
    : Raw.t_searchBuilder => {
  let builderWithLimit =
    switch (limit) {
    | Some(l) => Raw.limit'(builder, l)
    | None => builder
    };

  let builderWithSelect =
    switch (select) {
    | Some(cols) => Raw.select'(builderWithLimit, Array.fromList(cols))
    | None => builderWithLimit
    };

  switch (where) {
  | Some(condition) => Raw.where'(builderWithSelect, condition)
  | None => builderWithSelect
  };
};

/* Main API functions with IO monad for error handling */

/**
 * Connect to a LanceDB database
 */
let connect = (dbPath: string): IO.t(database, Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.connect'(dbPath))
  |> IO.map(db =>
       {
         db,
         path: dbPath,
       }
     );
};

/**
 * Create a new table with initial data
 */
let createTable =
    (
      {db, _}: database,
      tableName: string,
      data: list(recordData),
      overwrite: bool,
    )
    : IO.t(table, Js.Exn.t) => {
  let jsData = Array.fromList(List.map(recordDataToJs, data));
  let options = {writeMode: overwrite ? "overwrite" : "append"};
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.createTable'(db, tableName, jsData, options)
  )
  |> IO.map(table =>
       {
         table,
         name: tableName,
       }
     );
};

/**
 * Open an existing table
 */
let openTable =
    ({db, _}: database, tableName: string): IO.t(table, Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.openTable'(db, tableName))
  |> IO.map(table =>
       {
         table,
         name: tableName,
       }
     );
};

/**
 * Add data to an existing table
 */
let addToTable =
    ({table, _}: table, data: list(recordData)): IO.t(unit, Js.Exn.t) => {
  let jsData = Array.fromList(List.map(recordDataToJs, data));
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.add'(table, jsData));
};

/**
 * Search for similar vectors in a table
 */
let searchTable =
    ({table, _}: table, queryVector: list(float), options: searchOptions)
    : IO.t(searchResults, Js.Exn.t) => {
  let vectorArray = Array.fromList(queryVector);
  let builder = Raw.search'(table, vectorArray);
  let configuredBuilder = searchOptionsToBuilder(builder, options);
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.execute'(configuredBuilder))
  |> IO.map(Array.toList);
} /* }*/;

/* Default dependencies for testing */
// let defaultDependencies = {
//   connect,
//   createTable,
//   openTable,
//   addToTable,
//   searchTable,
