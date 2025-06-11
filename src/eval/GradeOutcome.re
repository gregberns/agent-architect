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

let readCompilationResults =
    (filePath: string): IO.t(Shared.CompilationResults.t, string) => {
  Shared.FileOps.readFileContents(filePath)
  |> IO.mapError(error =>
       "Failed to read file: "
       ++ (Js.Exn.message(error) |> Option.getOrElse("Unknown error"))
     )
  |> IO.flatMap(content => {
       switch (Utils.JsonUtils.parseSafe(content)) {
       | Some(_json) =>
         // Note: We need to implement a decoder for CompilationResults.t
         // For now, we'll need to handle this manually or extend Shared.re
         IO.throw("JSON decoding for CompilationResults not yet implemented")
       | None => IO.throw("Invalid JSON format in file: " ++ filePath)
       }
     });
};

// type x = {
//   promptHash: string,
//   promptTemplate: Shared.PromptTemplate.t,
//   scoreValues: array(int),
// };

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

// let gradeFromFile = (filePath: string): IO.t(TaskGradeReport.t, string) =>
//   ;

let writeGradeReport =
    (filePath: string, report: TaskGradeReport.t): IO.t(unit, string) => {
  let json = TaskGradeReport.encode(report);
  let content = Js.Json.stringify(json);

  Bindings.NodeJs.Fs.writeFileSyncRecursive(
    filePath,
    content,
    Bindings.NodeJs.Fs.makeWriteFileOptions(~flag=Write, ()),
  )
  |> IO.mapError(error =>
       "Failed to write file: "
       ++ (Js.Exn.message(error) |> Option.getOrElse("Unknown error"))
     );
};

let gradeAndWrite:
  (string, Shared.CompilationResults.t) => IO.t(unit, Shared.processError) =
  filePath =>
    gradeCompilationResults
    >> writeGradeReport(filePath)
    >> IO.mapError(e => `GradingError(e));

let processGradingFromFiles =
    (inputPath: string, outputPath: string): IO.t(unit, string) => {
  readCompilationResults(inputPath)
  |> IO.map(gradeCompilationResults)
  |> IO.flatMap(report => writeGradeReport(outputPath, report))
  |> IO.map(_ => {
       Printf.printf(
         "Grading completed. Results written to: %s\n",
         outputPath,
       )
     });
};
