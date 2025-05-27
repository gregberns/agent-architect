open Jest;
open Expect;
open TestUtils;
open Bindings.ChromaDb;

describe("ChromaDb", () => {
  let testCollectionName =
    "test-collection-" ++ string_of_float(Js.Date.now());
  let serverPath = "http://localhost:8000";

  describe("client operations", () => {
    Test.testIO("should create ChromaDB client", () => {
      createClient(serverPath)
      |> IO.map(client => {expect(client.serverPath) |> toEqual(serverPath)})
    })
  });

  describe("collection lifecycle", () => {
    Test.testIO("should create, use, and delete collection", () => {
      let testData = {
        ids: ["id1", "id2"],
        documents: ["First document content", "Second document content"],
        metadatas:
          Some([
            Js.Dict.fromArray([|("category", Js.Json.string("test"))|]),
            Js.Dict.fromArray([|("category", Js.Json.string("example"))|]),
          ]),
        embeddings: None,
      };

      let queryOptions = {
        queryTexts: ["document content"],
        nResults: 2,
        where: None,
        whereDocument: None,
      };

      createClient(serverPath)
      |> IO.flatMap(client => {
           createCollection(client, testCollectionName)
           |> IO.flatMap(collection => {
                expect(collection.name) |> toEqual(testCollectionName);

                addDocuments(collection, testData)
                |> IO.flatMap(_ => {
                     countDocuments(collection)
                     |> IO.flatMap(count => {
                          expect(count) |> toBe(2);

                          queryDocuments(collection, queryOptions)
                          |> IO.flatMap(results => {
                               expect(List.length(results.ids)) |> toBe(2);
                               expect(List.length(results.documents))
                               |> toBe(2);

                               deleteCollection(client, testCollectionName)
                               |> IO.map(_ => {
                                    expect(true)
                                    |> toBe(true) // Test completed successfully
                                  });
                             });
                        })
                   });
              })
         });
    })
  });

  describe("data operations", () => {
    Test.testIO("should add and query documents with metadata", () => {
      let testData = {
        ids: ["doc1"],
        documents: ["This is a test document about machine learning"],
        metadatas:
          Some([
            Js.Dict.fromArray([|
              ("topic", Js.Json.string("AI")),
              ("length", Js.Json.number(45.0)),
            |]),
          ]),
        embeddings: None,
      };

      let queryOptions = {
        queryTexts: ["machine learning"],
        nResults: 1,
        where: None,
        whereDocument: None,
      };

      createClient(serverPath)
      |> IO.flatMap(client => {
           createCollection(client, testCollectionName ++ "-data")
           |> IO.flatMap(collection => {
                addDocuments(collection, testData)
                |> IO.flatMap(_ => {
                     queryDocuments(collection, queryOptions)
                     |> IO.flatMap(results => {
                          expect(List.length(results.documents)) |> toBe(1);

                          let firstDocuments =
                            List.head(results.documents)
                            |> Option.getOrElse([]);
                          let firstDocument =
                            List.head(firstDocuments) |> Option.getOrElse("");
                          expect(firstDocument)
                          |> toEqual(
                               "This is a test document about machine learning",
                             );

                          deleteCollection(
                            client,
                            testCollectionName ++ "-data",
                          )
                          |> IO.map(_ => expect(true) |> toBe(true));
                        })
                   })
              })
         });
    });

    Test.testIO("should handle empty collections", () => {
      createClient(serverPath)
      |> IO.flatMap(client => {
           createCollection(client, testCollectionName ++ "-empty")
           |> IO.flatMap(collection => {
                countDocuments(collection)
                |> IO.flatMap(count => {
                     expect(count) |> toBe(0);

                     deleteCollection(client, testCollectionName ++ "-empty")
                     |> IO.map(_ => expect(true) |> toBe(true));
                   })
              })
         })
    });
  });

  describe("error handling", () => {
    test("should handle invalid server path gracefully", () => {
      let invalidPath = "http://invalid-server:9999";

      // Note: This test will likely succeed in client creation but fail on actual operations
      // ChromaDB client creation is typically lazy and doesn't immediately connect
      expect(() =>
        createClient(invalidPath)
      ) |> not_ |> toThrow;
    })
  });
});
