open Relude.Globals;

/**
 * TestProcess.re - Test the Process.re module with actual digest files
 */

/* Test function to process the test1.json file */
let testProcessDigestFile = () => {
  let digestFilePath = "./data/eval_output/test1.json";
  let outputDir = "./data/eval_output";

  Js.log("=== Testing Process.re Code Extraction ===");
  Js.log("Digest file: " ++ digestFilePath);
  Js.log("Output directory: " ++ outputDir);
  Js.log("");

  Eval.Process.processDigestFile(~digestFilePath, ~outputDir)
  |> IO.unsafeRunAsync(
       fun
       | Result.Ok(
           {extracted_files, total_files, processing_time}: Eval.Process.extractionResult,
         ) => {
           Js.log("✅ Extraction completed successfully!");
           Js.log(Printf.sprintf("Total files extracted: %d", total_files));
           Js.log(
             Printf.sprintf("Processing time: %.2f ms", processing_time),
           );
           Js.log("");
           Js.log("Extracted files:");
           Array.forEach(
             ({file_path, _}: Eval.Process.extractedCode) => {
               Js.log(Printf.sprintf("  - %s", file_path))
             },
             extracted_files,
           );
         }
       | Result.Error(error) => {
           let errorMessage =
             Eval.Process.ErrorUtils.processErrorToString(error);
           Js.log("❌ Extraction failed:");
           Js.log("  " ++ errorMessage);
         },
     );
};

/* Main entry point */
let () = {
  testProcessDigestFile();
};
