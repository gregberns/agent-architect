// open Jest;
  // open Expect;
  // open Bindings.LanceDb;
  //
  // ###############################################################
  //
  //  ALL THESE TESTS ARE SHIT
  //
  // ###############################################################
  //
  // describe("LanceDb", () => {
  //   describe("connect", () => {
  //     test("should connect to database successfully", () => {
  //       let mockDbPath = "./temp/test.db";
  //       let _result = connect(mockDbPath);
  //       // For now, we'll test that it returns an IO value
  //       // In a real test environment, we'd mock the external call
  //       expect(true) |> toBe(true);
  //     });
  //     test("should handle invalid database path", () => {
  //       let mockDbPath = "";
  //       let _result = connect(mockDbPath);
  //       // For now, we'll test that it returns an IO value
  //       expect(true) |> toBe(true);
  //     });
  //   });
  //   describe("createTable", () => {
  //     test("should create table with valid data", () => {
  //       let mockDb = {
  //         db: [%raw "{}"],
  //         path: "./temp/test.db",
  //       };
  //       let mockData = [
  //         {
  //           vector: [0.1, 0.2, 0.3],
  //           text: "test document",
  //           id: 1,
  //         },
  //       ];
  //       let _result = createTable(mockDb, "test_table", mockData, false);
  //       expect(true) |> toBe(true);
  //     });
  //     test("should handle empty data array", () => {
  //       let mockDb = {
  //         db: [%raw "{}"],
  //         path: "./temp/test.db",
  //       };
  //       let mockData = [];
  //       let _result = createTable(mockDb, "test_table", mockData, false);
  //       expect(true) |> toBe(true);
  //     });
  //   });
  //   describe("openTable", () => {
  //     test("should open existing table", () => {
  //       let mockDb = {
  //         db: [%raw "{}"],
  //         path: "./temp/test.db",
  //       };
  //       let _result = openTable(mockDb, "test_table");
  //       expect(true) |> toBe(true);
  //     });
  //     test("should handle non-existent table", () => {
  //       let mockDb = {
  //         db: [%raw "{}"],
  //         path: "./temp/test.db",
  //       };
  //       let _result = openTable(mockDb, "non_existent_table");
  //       expect(true) |> toBe(true);
  //     });
  //   });
  //   describe("addToTable", () => {
  //     test("should add data to table", () => {
  //       let mockTable = {
  //         table: [%raw "{}"],
  //         name: "test_table",
  //       };
  //       let mockData = [
  //         {
  //           vector: [0.1, 0.2, 0.3],
  //           text: "test document",
  //           id: 1,
  //         },
  //       ];
  //       let _result = addToTable(mockTable, mockData);
  //       expect(true) |> toBe(true);
  //     });
  //     test("should handle empty data array for add", () => {
  //       let mockTable = {
  //         table: [%raw "{}"],
  //         name: "test_table",
  //       };
  //       let mockData = [];
  //       let _result = addToTable(mockTable, mockData);
  //       expect(true) |> toBe(true);
  //     });
  //   });
  //   describe("searchTable", () => {
  //     test("should search table with options", () => {
  //       let mockTable = {
  //         table: [%raw "{}"],
  //         name: "test_table",
  //       };
  //       let mockVector = [0.1, 0.2, 0.3];
  //       let searchOptions = {
  //         limit: Some(10),
  //         select: Some(["id", "text"]),
  //         where: Some("id > 0"),
  //       };
  //       let _result = searchTable(mockTable, mockVector, searchOptions);
  //       expect(true) |> toBe(true);
  //     });
  //     test("should handle empty vector for search", () => {
  //       let mockTable = {
  //         table: [%raw "{}"],
  //         name: "test_table",
  //       };
  //       let mockVector = [];
  //       let searchOptions = {
  //         limit: None,
  //         select: None,
  //         where: None,
  //       };
  //       let _result = searchTable(mockTable, mockVector, searchOptions);
  //       expect(true) |> toBe(true);
  //     });
  //     test("should search with minimal options", () => {
  //       let mockTable = {
  //         table: [%raw "{}"],
  //         name: "test_table",
  //       };
  //       let mockVector = [0.1, 0.2, 0.3];
  //       let searchOptions = {
  //         limit: None,
  //         select: None,
  //         where: None,
  //       };
  //       let _result = searchTable(mockTable, mockVector, searchOptions);
  //       expect(true) |> toBe(true);
  //     });
  //   });
  // });
