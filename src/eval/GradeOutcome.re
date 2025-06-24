open Relude.Globals;

module GradeResult = {
  type score =
    | ParseFailure
    | CompileFailure
    | Success;

  type errors = {
    parseErrors: list(string),
    compileErrors: list(string),
    runtimeErrors: list(string),
    testErrors: list(string),
  };

  type t = {
    extractedCode: Shared.ExtractedCode.t,
    prompt: string,
    resultingCode: string,
    score,
    scoreValue: int,
    errors,
  };

  let scoreToInt = (score: score): int => {
    switch (score) {
    | ParseFailure => 0
    | CompileFailure => 1
    | Success => 2
    };
  };

  let calculateScore = (compilationResult: Shared.CompilationResult.t): score => {
    switch (compilationResult.parseError, compilationResult.compileError) {
    | ([], []) => Success
    | ([], _) => CompileFailure
    | (_, _) => ParseFailure
    };
  };

  let make =
      (compilationResult: Shared.CompilationResult.t, prompt: string): t => {
    let score = calculateScore(compilationResult);
    let scoreValue = scoreToInt(score);

    {
      extractedCode: compilationResult.extractedCode,
      prompt,
      resultingCode: compilationResult.extractedCode.content,
      score,
      scoreValue,
      errors: {
        parseErrors: compilationResult.parseError,
        compileErrors: compilationResult.compileError,
        runtimeErrors: compilationResult.runtimeError,
        testErrors: compilationResult.testError,
      },
    };
  };

  let encode = (gradeResult: t): Js.Json.t => {
    let scoreString =
      switch (gradeResult.score) {
      | ParseFailure => "parse_failure"
      | CompileFailure => "compile_failure"
      | Success => "success"
      };

    let encodeStringList = (lst: list(string)): Js.Json.t =>
      Js.Json.array(List.map(Js.Json.string, lst) |> List.toArray);

    Js.Json.object_(
      Js.Dict.fromList([
        (
          "extractedCode",
          Shared.ExtractedCode.encode(gradeResult.extractedCode),
        ),
        ("prompt", Js.Json.string(gradeResult.prompt)),
        ("resultingCode", Js.Json.string(gradeResult.resultingCode)),
        ("score", Js.Json.string(scoreString)),
        (
          "scoreValue",
          Js.Json.number(Float.fromInt(gradeResult.scoreValue)),
        ),
        (
          "errors",
          Js.Json.object_(
            Js.Dict.fromList([
              (
                "parseErrors",
                encodeStringList(gradeResult.errors.parseErrors),
              ),
              (
                "compileErrors",
                encodeStringList(gradeResult.errors.compileErrors),
              ),
              (
                "runtimeErrors",
                encodeStringList(gradeResult.errors.runtimeErrors),
              ),
              (
                "testErrors",
                encodeStringList(gradeResult.errors.testErrors),
              ),
            ]),
          ),
        ),
      ]),
    );
  };
};

module TaskGradeReport = {
  type statistics = {
    totalAttempts: int,
    parseFailures: int,
    compileFailures: int,
    successes: int,
    averageScore: float,
  };

  type gradeSummary = {
    promptTemplate: Shared.PromptTemplate.t,
    scores: array(int),
    averageScore: float,
  };

  type t = {
    executedAt: string,
    task: Shared.EvaluationTask.t,
    gradeResults: array(GradeResult.t),
    gradeSummaries: array(gradeSummary),
    totalFiles: int,
    processingTime: float,
    statistics,
  };

  let calculateStatistics = (gradeResults: array(GradeResult.t)) => {
    let totalAttempts = Array.length(gradeResults);
    let (parseFailures, compileFailures, successes) =
      Array.foldLeft(
        (
          (parseCount, compileCount, successCount),
          gradeResult: GradeResult.t,
        ) => {
          switch (gradeResult.score) {
          | GradeResult.ParseFailure => (
              parseCount + 1,
              compileCount,
              successCount,
            )
          | GradeResult.CompileFailure => (
              parseCount,
              compileCount + 1,
              successCount,
            )
          | GradeResult.Success => (
              parseCount,
              compileCount,
              successCount + 1,
            )
          }
        },
        (0, 0, 0),
        gradeResults,
      );

    let totalScore =
      Array.foldLeft(
        (acc, gradeResult: GradeResult.t) => acc + gradeResult.scoreValue,
        0,
        gradeResults,
      );

    let averageScore =
      totalAttempts > 0
        ? Float.fromInt(totalScore) /. Float.fromInt(totalAttempts) : 0.0;

    {
      totalAttempts,
      parseFailures,
      compileFailures,
      successes,
      averageScore,
    };
  };

  let make =
      (
        task: Shared.EvaluationTask.t,
        gradeResults: array(GradeResult.t),
        gradeSummaries,
        executedAt: string,
        totalFiles: int,
        processingTime: float,
      )
      : t => {
    let statistics = calculateStatistics(gradeResults);

    {
      task,
      gradeResults,
      gradeSummaries,
      executedAt,
      totalFiles,
      processingTime,
      statistics,
    };
  };

  let encodeGradeSummary = (summary: gradeSummary): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        (
          "promptTemplate",
          Shared.PromptTemplate.encode(summary.promptTemplate),
        ),
        ("averageScore", Js.Json.number(summary.averageScore)),
        (
          "scores",
          Js.Json.array(
            Array.map(Float.fromInt >> Js.Json.number, summary.scores),
          ),
        ),
      ]),
    );
  };

  let encode = (report: t): Js.Json.t => {
    Js.Json.object_(
      Js.Dict.fromList([
        ("task", Shared.EvaluationTask.encode(report.task)),
        (
          "gradeResults",
          Js.Json.array(Array.map(GradeResult.encode, report.gradeResults)),
        ),
        (
          "gradeSummary",
          Js.Json.array(
            Array.map(encodeGradeSummary, report.gradeSummaries),
          ),
        ),
        ("executedAt", Js.Json.string(report.executedAt)),
        ("totalFiles", Js.Json.number(Float.fromInt(report.totalFiles))),
        ("processingTime", Js.Json.number(report.processingTime)),
        (
          "statistics",
          Js.Json.object_(
            Js.Dict.fromList([
              (
                "totalAttempts",
                Js.Json.number(
                  Float.fromInt(report.statistics.totalAttempts),
                ),
              ),
              (
                "parseFailures",
                Js.Json.number(
                  Float.fromInt(report.statistics.parseFailures),
                ),
              ),
              (
                "compileFailures",
                Js.Json.number(
                  Float.fromInt(report.statistics.compileFailures),
                ),
              ),
              (
                "successes",
                Js.Json.number(Float.fromInt(report.statistics.successes)),
              ),
              (
                "averageScore",
                Js.Json.number(report.statistics.averageScore),
              ),
            ]),
          ),
        ),
      ]),
    );
  };
};

let gradeCompilationResults =
    (compilationResults: Shared.CompilationResults.t): TaskGradeReport.t => {
  let gradeResults =
    compilationResults.compilation_results
    |> Array.map((compilationResult: Shared.CompilationResult.t) => {
         // Find the corresponding prompt from prompt_results
         let prompt =
           switch (
             Array.find(
               (promptResult: Shared.PromptResult.t) =>
                 promptResult.promptTemplate.hash
                 == compilationResult.extractedCode.promptTemplate.hash,
               compilationResults.prompt_results,
             )
           ) {
           | Some(promptResult) => promptResult.prompt
           | None =>
             "Prompt not found for template_hash: "
             ++ compilationResult.extractedCode.promptTemplate.hash
           };

         GradeResult.make(compilationResult, prompt);
       });

  let gradeSummaries =
    gradeResults
    |> Array.foldLeft(
         (
           acc,
           {
             scoreValue,
             extractedCode: {promptTemplate: {hash, _} as promptTemplate, _},
             _,
           }: GradeResult.t,
         ) =>
           acc
           |> String.Map.update(
                hash,
                Option.map(((prompt, scores)) =>
                  (prompt, scores |> Array.append(scoreValue))
                )
                >> Option.getOrElse((promptTemplate, [|scoreValue|]))
                >> Option.pure,
              ),
         String.Map.make(),
       )
    |> String.Map.valueArray
    |> Array.map(
         ((promptTemplate: Shared.PromptTemplate.t, scores: array(int))): TaskGradeReport.gradeSummary => {
         {
           promptTemplate,
           scores,
           averageScore: scores |> Utils.NumberUtils.avg,
         }
       });

  TaskGradeReport.make(
    compilationResults.task,
    gradeResults,
    gradeSummaries,
    compilationResults.executed_at,
    compilationResults.total_files,
    compilationResults.processing_time,
  );
};

let writeGradeReport =
    (filePath: string, report: TaskGradeReport.t)
    : IO.t(unit, Shared.processError) => {
  let json = TaskGradeReport.encode(report);
  let content = Js.Json.stringify(json);

  Bindings.NodeJs.Fs.writeFileSyncRecursive(
    filePath,
    content,
    Bindings.NodeJs.Fs.makeWriteFileOptions(~flag=Write, ()),
  )
  // |> IO.mapError(error =>
  //      "Failed to write file: "
  //      ++ (Js.Exn.message(error) |> Option.getOrElse("Unknown error"))
  //    )
  |> IO.mapError(e =>
       `GradingError(
         "Failed to write file writeGradeReport: "
         ++ (Js.Exn.message(e) |> Option.getOrElse("Unknown error")),
       )
     );
};

let taskSummary = ({gradeSummaries, _}: TaskGradeReport.t) => {
  gradeSummaries
  |> Array.map(
       (
         {averageScore, scores, promptTemplate: {hash, name, prompt}, _}: TaskGradeReport.gradeSummary,
       ) => {
       let scores =
         scores |> Array.map(Int.toString) |> Array.String.intercalate(", ");
       let averageScore = averageScore |> Float.toString;
       {j|Prompt Name: $name (hash: $hash)
Prompt: $prompt
Scores: $scores
Average Score: $averageScore|j};
     })
  |> Array.String.intercalate("\n\n")
  |> String.concat({||});
};

let gradeAndWrite:
  (string, Shared.CompilationResults.t) =>
  IO.t(TaskGradeReport.t, Shared.processError) =
  filePath =>
    gradeCompilationResults
    >> (report => writeGradeReport(filePath, report) |> IO.map(() => report));

/* Generate markdown summary from array of task grade reports */
let generateMarkdownSummary =
    (reports: array(TaskGradeReport.t), epoch: string): string => {
  // Extract prompt information from the first report (assuming all tasks use same prompts)
  let _promptInfo =
    switch (Array.head(reports)) {
    | Some(firstReport) =>
      firstReport.gradeSummaries
      |> Array.map(({promptTemplate, _}: TaskGradeReport.gradeSummary) =>
           Printf.sprintf(
             "- **%s** (hash: %s)\n  - Prompt: %s",
             promptTemplate.name,
             promptTemplate.hash,
             promptTemplate.prompt,
           )
         )
      |> Array.String.intercalate("\n")
    | None => "No reports available"
    };

  // Calculate overall statistics
  let totalTasks = Array.length(reports);
  let totalAttempts =
    Array.foldLeft(
      (acc, report: TaskGradeReport.t) =>
        acc + report.statistics.totalAttempts,
      0,
      reports,
    );
  let totalScoreSum =
    Array.foldLeft(
      (acc, report: TaskGradeReport.t) =>
        acc
        +. report.statistics.averageScore
        *. Float.fromInt(report.statistics.totalAttempts),
      0.0,
      reports,
    );
  let overallAverageScore =
    totalAttempts > 0 ? totalScoreSum /. Float.fromInt(totalAttempts) : 0.0;

  // Get prompt iterations from first report
  let promptIterations =
    switch (Array.head(reports)) {
    | Some(firstReport) =>
      switch (Array.head(firstReport.gradeSummaries)) {
      | Some(summary) => Array.length(summary.scores)
      | None => 0
      }
    | None => 0
    };

  // Generate per-prompt performance analysis
  let promptAnalysis =
    switch (Array.head(reports)) {
    | Some(firstReport) =>
      firstReport.gradeSummaries
      |> Array.map(({promptTemplate, _}: TaskGradeReport.gradeSummary) => {
           // Collect all scores for this prompt across all tasks
           let allScoresForPrompt =
             reports
             |> Array.flatMap((report: TaskGradeReport.t) =>
                  report.gradeSummaries
                  |> Array.filter((summary: TaskGradeReport.gradeSummary) =>
                       summary.promptTemplate.hash == promptTemplate.hash
                     )
                  |> Array.flatMap((summary: TaskGradeReport.gradeSummary) =>
                       summary.scores
                     )
                );

           // Collect all grade results for this prompt across all tasks
           let allGradeResultsForPrompt =
             reports
             |> Array.flatMap((report: TaskGradeReport.t) =>
                  report.gradeResults
                  |> Array.filter((gradeResult: GradeResult.t) =>
                       gradeResult.extractedCode.promptTemplate.hash
                       == promptTemplate.hash
                     )
                );

           // Calculate statistics for this prompt
           let totalAttempts = Array.length(allScoresForPrompt);
           let totalScore = Array.foldLeft((+), 0, allScoresForPrompt);
           let averageScore =
             totalAttempts > 0
               ? Float.fromInt(totalScore) /. Float.fromInt(totalAttempts)
               : 0.0;

           // Count success rates
           let parseFailures =
             Array.filter(score => score == 0, allScoresForPrompt)
             |> Array.length;
           let partialSuccesses =
             Array.filter(score => score == 1, allScoresForPrompt)
             |> Array.length;
           let fullSuccesses =
             Array.filter(score => score == 2, allScoresForPrompt)
             |> Array.length;

           let formatErrorList =
             Array.map(String.concat("\t* "))
             >> Array.String.intercalate("\n");

           // Aggregate errors by type
           let allParseErrors: string =
             allGradeResultsForPrompt
             |> Array.flatMap((gradeResult: GradeResult.t) =>
                  gradeResult.errors.parseErrors |> List.toArray
                )
             |> formatErrorList;

           let allCompileErrors =
             allGradeResultsForPrompt
             |> Array.flatMap((gradeResult: GradeResult.t) =>
                  gradeResult.errors.compileErrors |> List.toArray
                )
             |> formatErrorList;

           let allRuntimeErrors =
             allGradeResultsForPrompt
             |> Array.flatMap((gradeResult: GradeResult.t) =>
                  gradeResult.errors.runtimeErrors |> List.toArray
                )
             |> formatErrorList;

           let allTestErrors =
             allGradeResultsForPrompt
             |> Array.flatMap((gradeResult: GradeResult.t) =>
                  gradeResult.errors.testErrors |> List.toArray
                )
             |> formatErrorList;

           let errorMessageBlock =
             Printf.sprintf(
               {|**Parse Errors:**
%s

**Compile Errors:**
%s

**Runtime Errors:**
%s

**Test Errors:**
%s
|},
               allParseErrors,
               allCompileErrors,
               allRuntimeErrors,
               allTestErrors,
             );

           let parseFailureRate =
             Float.fromInt(parseFailures)
             /. Float.fromInt(totalAttempts)
             *. 100.0;
           let partialSuccessRate =
             Float.fromInt(partialSuccesses)
             /. Float.fromInt(totalAttempts)
             *. 100.0;
           let fullSuccessRate =
             Float.fromInt(fullSuccesses)
             /. Float.fromInt(totalAttempts)
             *. 100.0;

           // Find best and worst performing tasks for this prompt
           let taskPerformances =
             reports
             |> List.fromArray
             |> List.map((report: TaskGradeReport.t) => {
                  let promptSummary =
                    report.gradeSummaries
                    |> Array.find((summary: TaskGradeReport.gradeSummary) =>
                         summary.promptTemplate.hash == promptTemplate.hash
                       );
                  switch (promptSummary) {
                  | Some(summary) =>
                    Some((report.task.task_id, summary.averageScore))
                  | None => None
                  };
                })
             |> List.mapOption(x => x)
             |> List.sortBy(((_, scoreA), (_, scoreB)) =>
                  Float.compare(scoreB, scoreA)
                )
             |> List.toArray;

           let bestTask = Array.head(taskPerformances);
           let worstTask = Array.last(taskPerformances);

           let overallPerformance =
             Printf.sprintf(
               {|- Average Score: %.2f
- Total Attempts: %d
- Parse Failure Rate: %.1f%% (%d failures)
- Partial Success Rate: %.1f%% (%d partial)
- Full Success Rate: %.1f%% (%d full)
|},
               averageScore,
               totalAttempts,
               parseFailureRate,
               parseFailures,
               partialSuccessRate,
               partialSuccesses,
               fullSuccessRate,
               fullSuccesses,
             );

           Printf.sprintf(
             {|### %s (hash: %s)

**Overall Performance:**
%s

**Task Performance:**
- Best Task: %s
- Worst Task: %s

**Analysis Notes:**
%s

#### Error Messages
%s

**Prompt Template:**
```
%s
```
|},
             promptTemplate.name,
             promptTemplate.hash,
             overallPerformance,
             switch (bestTask) {
             | Some((taskId, score)) =>
               Printf.sprintf("Task %d (%.2f)", taskId, score)
             | None => "None"
             },
             switch (worstTask) {
             | Some((taskId, score)) =>
               Printf.sprintf("Task %d (%.2f)", taskId, score)
             | None => "None"
             },
             if (parseFailureRate > 50.0) {
               "HIGH PARSE FAILURE RATE - Consider improving ReasonML syntax guidance";
             } else if (fullSuccessRate > 70.0) {
               "STRONG PERFORMANCE - This prompt template works well";
             } else if (partialSuccessRate > 50.0) {
               "MODERATE PERFORMANCE - Consider refining logic guidance";
             } else {
               "NEEDS IMPROVEMENT - Consider major prompt restructuring";
             },
             errorMessageBlock,
             promptTemplate.prompt,
           );
         })
      |> Array.String.intercalate("\n\n")
    | None => "No prompt analysis available"
    };

  // Generate task-specific results
  let taskResults =
    reports
    |> Array.map((report: TaskGradeReport.t) => {
         let taskId = report.task.task_id;
         let taskName =
           String.length(report.task.text) > 100
             ? String.slice(0, 100, report.task.text) ++ "..."
             : report.task.text;

         let promptResults =
           report.gradeSummaries
           |> Array.map(
                (
                  {promptTemplate, scores, averageScore, _}: TaskGradeReport.gradeSummary,
                ) => {
                let scoresStr =
                  scores
                  |> Array.map(Int.toString)
                  |> Array.String.intercalate(", ");
                Printf.sprintf(
                  "    - **%s**: Average: %.2f, Scores: [%s]",
                  promptTemplate.name,
                  averageScore,
                  scoresStr,
                );
              })
           |> Array.String.intercalate("\n");

         Printf.sprintf(
           "### Task %d\n\n**Description:** %s\n\n**Results:**\n%s\n\n**Overall Task Average:** %.2f\n",
           taskId,
           taskName,
           promptResults,
           report.statistics.averageScore,
         );
       })
    |> Array.String.intercalate("\n");

  let summary =
    Printf.sprintf(
      {|## Summary

- **Total Tasks:** %d
- **Total Attempts:** %d
- **Prompt Iterations per Task:** %d
- **Overall Average Score:** %.2f|},
      totalTasks,
      totalAttempts,
      promptIterations,
      overallAverageScore,
    );

  Printf.sprintf(
    {|# Evaluation Report - %s

%s



## Prompt Performance Analysis

%s

## Task Results

%s

---

*Generated on %s*
|},
    epoch,
    summary,
    //     ## Prompts Used
    // %s
    // promptInfo,
    promptAnalysis,
    taskResults,
    Js.Date.make() |> Js.Date.toISOString,
  );
};

/* Write markdown summary to file */
let writeSummaryMarkdown =
    (epoch: string, reportPath: string, reports: array(TaskGradeReport.t))
    : IO.t(unit, Shared.processError) => {
  let markdownContent = generateMarkdownSummary(reports, epoch);

  Bindings.NodeJs.Fs.writeFileSyncRecursive(
    reportPath,
    markdownContent,
    Bindings.NodeJs.Fs.makeWriteFileOptions(~flag=Write, ()),
  )
  |> IO.mapError(e =>
       `GradingError(
         "Failed to write markdown summary: "
         ++ (Js.Exn.message(e) |> Option.getOrElse("Unknown error")),
       )
     );
};

// let processGradingFromFiles =
//     (inputPath: string, outputPath: string): IO.t(unit, Shared.processError) => {
//   readCompilationResults(inputPath)
//   |> IO.map(gradeCompilationResults)
//   |> IO.flatMap(report => writeGradeReport(outputPath, report))
//   |> IO.map(_ => {
//        Printf.printf(
//          "Grading completed. Results written to: %s\n",
//          outputPath,
//        )
//      });
// };
