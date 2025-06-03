open Relude.Globals;

/**
 * Ingest.re - JSONL file processing for evaluation data
 *
 * Reads .jsonl files and parses JSON objects with the evaluation task structure.
 * This module now uses the shared types and utilities from Shared.re.
 */
/* Re-export shared types and modules for backward compatibility */

/* Re-export main functions using shared implementations */
let readFileContents = Shared.FileOps.readFileContents;
let splitLines = Shared.JsonlOps.splitLines;
let parseJsonLine = Shared.JsonlOps.parseJsonLine;
let parseJsonlLines = Shared.JsonlOps.parseJsonlLines;
let readJsonlFile = Shared.JsonlOps.readJsonlFile;

/* Helper function to read JSONL file with error handling */
let readJsonlFileWithErrorHandling =
    (filePath: string): IO.t(array(Shared.EvaluationTask.t), string) => {
  readJsonlFile(filePath)
  |> IO.mapError(Shared.ErrorUtils.jsonlParseErrorToString);
};

/* Example usage functions using shared implementations */
let loadEvaluationDataset = Shared.loadEvaluationDataset;
let processEvaluationFile = Shared.processEvaluationFile;

/* Validation helpers using shared implementations */
let validateTaskStructure = Shared.EvaluationTask.validateTaskStructure;
let validateAllTasks = Shared.EvaluationTask.validateAllTasks;
