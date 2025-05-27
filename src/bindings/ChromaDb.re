open Relude.Globals;

/**
 * ChromaDB bindings for Melange/ReasonML
 * Provides type-safe access to ChromaDB JavaScript client
 */

type t_chromaClient;

/* Configuration types */
type clientConfig = {
  [@mel.as "path"]
  path: string,
};

type collectionConfig = {
  [@mel.as "name"]
  name: string,
};

/* Data types for ChromaDB operations */
type addRequest = {
  [@mel.as "ids"]
  ids: array(string),
  [@mel.as "documents"]
  documents: array(string),
  [@mel.as "metadatas"]
  metadatas: Js.Nullable.t(array(Js.Dict.t(Js.Json.t))),
  [@mel.as "embeddings"]
  embeddings: Js.Nullable.t(array(array(float))),
};

type queryRequest = {
  [@mel.as "queryTexts"]
  queryTexts: array(string),
  [@mel.as "nResults"]
  nResults: int,
  [@mel.as "where"]
  where: Js.Nullable.t(Js.Dict.t(Js.Json.t)),
  [@mel.as "whereDocument"]
  whereDocument: Js.Nullable.t(Js.Dict.t(Js.Json.t)),
};

type queryResult = {
  [@mel.as "ids"]
  ids: array(array(string)),
  [@mel.as "documents"]
  documents: array(array(string)),
  [@mel.as "metadatas"]
  metadatas: array(array(Js.Nullable.t(Js.Dict.t(Js.Json.t)))),
  [@mel.as "distances"]
  distances: array(array(float)),
  [@mel.as "embeddings"]
  embeddings: Js.Nullable.t(array(array(array(float)))),
};

/* External bindings to ChromaDB JavaScript client */
module Raw = {
  /* ChromaClient class */
  [@mel.module "chromadb"] [@mel.new]
  external createClient': clientConfig => t_chromaClient = "ChromaClient";

  /* Collection operations */
  [@mel.send]
  external createCollection':
    ('chromaClient, collectionConfig) => Js.Promise.t('collection) =
    "createCollection";

  [@mel.send]
  external getCollection':
    ('chromaClient, collectionConfig) => Js.Promise.t('collection) =
    "getCollection";

  [@mel.send]
  external deleteCollection':
    ('chromaClient, collectionConfig) => Js.Promise.t(unit) =
    "deleteCollection";

  [@mel.send]
  external listCollections':
    'chromaClient => Js.Promise.t(array('collectionInfo)) =
    "listCollections";

  /* Collection data operations */
  [@mel.send]
  external add': ('collection, addRequest) => Js.Promise.t(unit) = "add";

  [@mel.send]
  external query': ('collection, queryRequest) => Js.Promise.t(queryResult) =
    "query";

  [@mel.send] external count': 'collection => Js.Promise.t(int) = "count";

  type peekConfig = {
    [@mel.as "limit"]
    limit: int,
  };

  [@mel.send]
  external peek': ('collection, peekConfig) => Js.Promise.t('peekResult) =
    "peek";

  type deleteConfig = {
    [@mel.as "ids"]
    ids: array(string),
  };

  [@mel.send]
  external deleteItems': ('collection, deleteConfig) => Js.Promise.t(unit) =
    "delete";
};

/* ReasonML-friendly wrapper types and functions */
type chromaClient = {
  client: t_chromaClient,
  serverPath: string,
};

type t_collection;

type collection = {
  collection: t_collection,
  name: string,
};

type addData = {
  ids: list(string),
  documents: list(string),
  metadatas: option(list(Js.Dict.t(Js.Json.t))),
  embeddings: option(list(list(float))),
};

type queryOptions = {
  queryTexts: list(string),
  nResults: int,
  where: option(Js.Dict.t(Js.Json.t)),
  whereDocument: option(Js.Dict.t(Js.Json.t)),
};

type queryResults = {
  ids: list(list(string)),
  documents: list(list(string)),
  metadatas: list(list(option(Js.Dict.t(Js.Json.t)))),
  distances: list(list(float)),
  embeddings: option(list(list(list(float)))),
};

/* Helper functions to convert between ReasonML and JavaScript types */
let addDataToJs =
    ({ids, documents, metadatas, embeddings, _}: addData): addRequest => {
  ids: Array.fromList(ids),
  documents: Array.fromList(documents),
  metadatas: metadatas |> Option.map(List.toArray) |> Js.Nullable.fromOption,
  embeddings:
    embeddings
    |> Option.map(List.map(List.toArray))
    |> Option.map(List.toArray)
    |> Js.Nullable.fromOption,
};

let queryOptionsToJs =
    ({queryTexts, nResults, where, whereDocument, _}: queryOptions)
    : queryRequest => {
  queryTexts: Array.fromList(queryTexts),
  nResults,
  where: where |> Js.Nullable.fromOption,
  whereDocument: whereDocument |> Js.Nullable.fromOption,
};

let queryResultFromJs =
    ({ids, documents, metadatas, distances, embeddings, _}: queryResult)
    : queryResults => {
  ids: Array.toList(ids) |> List.map(Array.toList),
  documents: Array.toList(documents) |> List.map(Array.toList),
  metadatas:
    Array.toList(metadatas)
    |> List.map(Array.toList)
    |> List.map(List.map(Js.Nullable.toOption)),
  distances: Array.toList(distances) |> List.map(Array.toList),
  embeddings:
    embeddings
    |> Js.Nullable.toOption
    |> Option.map(Array.toList)
    |> Option.map(List.map(Array.toList))
    |> Option.map(List.map(List.map(Array.toList))),
};

/* Main API functions with IO monad for error handling */

/**
 * Create a new ChromaDB client
 */
let createClient = (serverPath: string): IO.t(chromaClient, Js.Exn.t) =>
  IO.triesJS(() => {
    let config = {path: serverPath};
    let client = Raw.createClient'(config);
    {
      client,
      serverPath,
    };
  });

/**
 * Create a new collection
 */
let createCollection =
    ({client, _}: chromaClient, name: string): IO.t(collection, Js.Exn.t) => {
  let config = {name: name};
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.createCollection'(client, config)
  )
  |> IO.map(collection =>
       {
         collection,
         name,
       }
     );
};

/**
 * Get an existing collection
 */
let getCollection =
    ({client, _}: chromaClient, name: string): IO.t(collection, Js.Exn.t) => {
  let config = {name: name};
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.getCollection'(client, config))
  |> IO.map(collection =>
       {
         collection,
         name,
       }
     );
};

/**
 * Delete a collection
 */
let deleteCollection =
    ({client, _}: chromaClient, name: string): IO.t(unit, Js.Exn.t) => {
  let config = {name: name};
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.deleteCollection'(client, config)
  );
};

/**
 * List all collections
 */
let listCollections =
    ({client, _}: chromaClient): IO.t(array('collectionInfo), Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.listCollections'(client));
};

/**
 * Add documents to a collection
 */
let addDocuments =
    ({collection, _}: collection, data: addData): IO.t(unit, Js.Exn.t) => {
  let jsData = addDataToJs(data);
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.add'(collection, jsData));
};

/**
 * Query documents from a collection
 */
let queryDocuments =
    ({collection, _}: collection, options: queryOptions)
    : IO.t(queryResults, Js.Exn.t) => {
  let jsOptions = queryOptionsToJs(options);
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.query'(collection, jsOptions))
  |> IO.map(queryResultFromJs);
};

/**
 * Count documents in a collection
 */
let countDocuments = ({collection, _}: collection): IO.t(int, Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() => Raw.count'(collection));
};

/**
 * Peek at documents in a collection
 */
let peekDocuments =
    ({collection, _}: collection, limit: int): IO.t('peekResult, Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.peek'(collection, {limit: limit})
  );
};

/**
 * Delete documents from a collection
 */
let deleteDocuments =
    ({collection, _}: collection, ids: list(string)): IO.t(unit, Js.Exn.t) => {
  Utils.IOUtils.fromPromiseWithJsExn(() =>
    Raw.deleteItems'(collection, {ids: Array.fromList(ids)})
  );
};

// /* Default dependencies for testing */
// let defaultDependencies = {
//   createClient,
//   createCollection,
//   getCollection,
//   deleteCollection,
//   addDocuments,
//   queryDocuments,
//   countDocuments,
//   deleteDocuments,
// };
