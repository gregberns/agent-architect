open Relude.Globals;

/**
 * TestProcess.re - Test the Process.re module with actual digest files
 */

/* Test function to process the test1.json file */
let testProcessDigestFile = () => {
  let modelResponseOutputPath = "./data/evaluation/outputs/runs/001_2025-06-04_09-00-00/task_601.json";
  let compilePath = "./data/evaluation/outputs/scratch/001_2025-06-04_09-00-00";
  let codeValidationResultsPath = "./data/evaluation/outputs/test-results/001_2025-06-04_09-00-00";
  let gradedResultsPath = "./data/evaluation/outputs/test-results-graded/001_2025-06-04_09-00-00";

  Js.log("=== Testing Process.re Code Extraction ===");
  Js.log("Digest file: " ++ modelResponseOutputPath);
  Js.log("Code file directory: " ++ compilePath);
  Js.log("Code validation results: " ++ codeValidationResultsPath);
  Js.log("");

  // digest: Process Model Outputs -> Write outputs to disk
  Eval.GenerateFiles.processDigestFile(
    ~digestFilePath=modelResponseOutputPath,
    ~outputDir=compilePath,
  )
  // |> IO.bitap(
  //      (
  //        {extracted_files, total_files, processing_time}: Eval.GenerateFiles.extractionResult,
  //      ) => {
  //        Js.log("✅ Extraction completed successfully!");
  //        Js.log(Printf.sprintf("Total files extracted: %d", total_files));
  //        Js.log(Printf.sprintf("Processing time: %.2f ms", processing_time));
  //        Js.log("");
  //        Js.log("Extracted files:");
  //        Array.forEach(
  //          ({file_path, _}: Eval.Shared.ExtractedCode.t) => {
  //            Js.log(Printf.sprintf("  - %s", file_path))
  //          },
  //          extracted_files,
  //        );
  //      },
  //      error => {
  //        let errorMessage =
  //          Eval.Shared.ErrorUtils.processErrorToString(error);
  //        Js.log("❌ Extraction failed:");
  //        Js.log("  " ++ errorMessage);
  //      },
  //    )
  |> IO.flatMap(
       Eval.CompilationCheck.checkFiles(
         ~compilePath,
         ~codeValidationResultsPath,
       )
       >> IO.mapError(e =>
            `CompilationError(
              e
              |> Js.Exn.message
              |> Option.getOrElse("<<NO COMPILE ERROR MESSAGE>>"),
            )
          ),
     )
  |> IO.flatMap(
       Eval.GradeOutcome.gradeAndWrite(gradedResultsPath)
       >> IO.mapError(e => `GradingError(e)),
     )
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(_) => {
           Js.log("$$$$$$$ Complete");
         }
       | Result.Error(error) => {
           //  let errorMessage =
           //    Eval.Shared.ErrorUtils.processErrorToString(error);
           Js.log2(
             "❌ Extraction failed:",
             error,
             //  Js.log("  " ++ errorMessage);
           );
         },
     );
};

/* Main entry point */
let () = {
  testProcessDigestFile();
};

/*

 * evaluation
   * inputs
     * prompt-runs
       * 001_prompt-attempt (.json/yml containing the prompts)
         (may also want to point to the data to injest: mbpp.jsonl + rows)
     * source-data
       * mbpp.jsonl

   * outputs
     * runs (contains LLM outputs)
       * 001_YYYY-MM-DD_HH-mm-ss
         * task_XXX
     * scratch
       * 001_YYYY-MM-DD_HH-mm-ss  (should be the same name as the run, because outcome is deterministic for now)
         * task_XXX
           * (task.json)
           * (.re files)
     * test-results
       * 001_YYYY-MM-DD_HH-mm-ss

 */
