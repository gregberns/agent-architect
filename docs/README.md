










## Initial Discovery

Initial Prompt
```
I've been using Claude Code to build out an application and I'm seeing where it runs into challenges - one specifically being that it doesn't follow industry best practices or understand or do abstraction in many of the places that are critical when building larger applications. This is resulting in many bugs and problems.
I'd like to build an agent that is tasked with passing through the code base as it evolves to find and identify issues like anti-patterns, lack of tests, lack of DRY, database transactions being handled manually, etc.
I've played with smolagent and AI Crew - which were OK. I'd like something that could operate somewhat autonomously, meaning it can break the whole application down into sub sections, understand and document how each part relates to other parts (some of this is already done in the generated docs). Then it probably needs to focus on particular areas and find repeated patterns, anti-patterns, etc, and document that they're an issue. In a second pass, or as another task, it'll need to propose changes and document what needs to be done. That work should then be allocated to another worker task that can actually coordinate and execute the changes.
I'd like help putting a comprehensive plan together on how to structure something like this.
There are quite a few parts to executing this. I need an agent framework, I'm thinking LangChain and LangGraph. A way of breaking this down into one or more agents which will do particular tasks. A set of tasks and prompts that the agents will execute on. The agents will need tools - example: I'm using a task manager which has an MCP client so the agents can create task lists and execute on them. It needs to have a prioritization mechanizm built in - so once issues are identified, maybe those can be triaged and that process needs to understand how to prioritize one area over another.
Lets get started by creating an overview of the problem, breaking down the pieces and creating research areas and tasks in those areas that need to be executed on. Treat this as research and the more information and analysis the better.
```



```
Okay, this is an ambitious and highly valuable project. Automating code quality assurance and refactoring with AI agents is a cutting-edge area. Let's break this down into a comprehensive plan.

**Project Title:** "CodeGuardian AI: Autonomous Code Quality & Refactoring System"

**1. Overview of the Problem & Goal**

*   **Problem:** LLM-generated code (like from Claude) often lacks adherence to software engineering best practices, leading to:
    *   Anti-patterns (e.g., God objects, spaghetti code).
    *   Lack of DRY (Don't Repeat Yourself).
    *   Insufficient or missing unit/integration tests.
    *   Manual handling of critical operations (e.g., database transactions, resource management).
    *   Poor abstraction and modularity.
    *   Increased bug density, maintenance overhead, and difficulty scaling.
*   **Goal:** To develop an autonomous multi-agent system (CodeGuardian AI) that continuously analyzes a evolving codebase, identifies violations of best practices, proposes and prioritizes refactoring solutions, and coordinates their implementation (potentially with human oversight or via automated tasks).

**2. Core Components & Agent Architecture (Leveraging LangChain & LangGraph)**

We'll design a system of specialized agents communicating and collaborating through LangGraph, which is excellent for building cyclical, stateful agentic applications.

*   **A. Code Ingestion & Representation Layer:**
    *   **Codebase Monitor Agent:**
        *   **Responsibility:** Watches the codebase (e.g., Git repository) for changes.
        *   **Triggers:** New commits, pull requests.
        *   **Action:** Fetches updated code files.
    *   **Code Parser & Indexer Agent:**
        *   **Responsibility:** Parses the code into a structured representation and indexes it for efficient retrieval and analysis.
        *   **Tools:**
            *   AST (Abstract Syntax Tree) parsers (e.g., `tree-sitter` for various languages, Python's `ast` module).
            *   Vector Database (e.g., ChromaDB, FAISS, Weaviate) for semantic search on code chunks, docstrings, comments.
            *   Graph Database (e.g., Neo4j - optional but powerful) to store relationships between code elements (classes, functions, modules, dependencies).
        *   **Action:**
            1.  Generates ASTs for modified/new files.
            2.  Chunks code and associated documentation (if available) for vector embedding.
            3.  Updates the vector and graph databases.
            4.  Extracts high-level structural information (module dependencies, class hierarchies).

*   **B. Analysis & Issue Identification Layer:**
    *   **Architectural Analyst Agent:**
        *   **Responsibility:** Understands the overall application structure, component interactions, and data flow. Reconciles this with existing documentation.
        *   **Input:** Code structure from Parser/Indexer, existing documentation.
        *   **Action:**
            1.  Builds/updates a conceptual model of the application architecture.
            2.  Identifies high-level architectural smells (e.g., cyclical dependencies, overly complex modules).
            3.  Uses the vector DB to find semantically similar code sections across the application.
        *   **Prompt Focus:** "Analyze the dependencies between these modules. Are there any circular dependencies? Is module X becoming a God module?"
    *   **Pattern Detection Agent (or multiple specialized agents):**
        *   **Responsibility:** Scans code for specific anti-patterns, bad practices, and lack of good practices.
        *   **Input:** Code snippets, ASTs, architectural context from Architectural Analyst.
        *   **Sub-Agents / Specialized Focus Areas:**
            *   **DRY Violation Detector:** Finds duplicated or highly similar code blocks.
            *   **Test Coverage Analyst:** Checks for missing tests for public methods/functions (can use heuristics or integrate with coverage tools).
            *   **Transaction Management Auditor:** Looks for manual database commit/rollback patterns instead of context managers or decorators.
            *   **Abstraction & Encapsulation Critic:** Identifies areas with poor abstraction, leaky abstractions, or violations of encapsulation.
            *   **Security Vulnerability Scanner (Basic):** Looks for common OWASP Top 10 vulnerabilities (e.g., SQL injection patterns, hardcoded secrets). Could integrate with linters or static analysis security testing (SAST) tools.
            *   **Readability & Maintainability Agent:** Assesses code complexity (e.g., cyclomatic complexity from ASTs), naming conventions, comment quality.
        *   **Tools:**
            *   Linters (ESLint, Pylint, RuboCop, etc.) - results can be fed to the agent.
            *   Static analysis tools.
            *   Custom LLM prompts tailored for specific patterns.
        *   **Action:** Identifies and documents specific instances of issues with file paths, line numbers, and a description of the problem.
        *   **Prompt Focus:** "Given this function `<code>` and its context, does it exhibit the 'manual database transaction handling' anti-pattern? Explain why or why not." or "Compare these two code blocks `<code>` and `<code2>`. Are they significantly similar? Could they be refactored for DRY?"

*   **C. Solution & Prioritization Layer:**
    *   **Refactoring Strategist Agent:**
        *   **Responsibility:** Proposes concrete, actionable refactoring solutions for identified issues.
        *   **Input:** Documented issues from Pattern Detection Agents, architectural context.
        *   **Action:**
            1.  For each issue, generates one or more potential refactoring solutions (e.g., "Extract method X", "Introduce class Y", "Use try-with-resources for Z", "Wrap DB calls in a transaction decorator").
            2.  Provides before/after code examples (or diffs).
            3.  Explains the benefits of the proposed change.
        *   **Prompt Focus:** "For the identified DRY violation between `file_A:line_X` and `file_B:line_Y`, propose a refactoring to a shared utility function. Provide the new function and how the original locations should call it."
    *   **Triage & Prioritization Agent:**
        *   **Responsibility:** Evaluates the severity, impact, and effort of identified issues and proposed solutions to prioritize them.
        *   **Input:** List of issues and proposed solutions.
        *   **Criteria for Prioritization (configurable):**
            *   **Severity:** Critical (e.g., security flaw, data corruption risk), High (e.g., major bug potential, performance bottleneck), Medium (e.g., maintainability issue), Low (e.g., minor style issue).
            *   **Impact:** How widespread is the issue? How many parts of the system does it affect?
            *   **Effort:** Estimated complexity/time to implement the fix.
            *   **Dependencies:** Are there other issues that need to be fixed first?
            *   **Frequency:** How often does this anti-pattern appear?
        *   **Action:**
            1.  Assigns a priority score to each issue/solution.
            2.  Groups related issues that could be tackled together.
        *   **Prompt Focus:** "Given this issue: 'Manual DB transaction in PaymentService', and its potential impact: 'Data inconsistency on payment failure', and estimated effort: 'Low', assign a priority level (Critical, High, Medium, Low) and justify."

*   **D. Execution & Coordination Layer:**
    *   **Task Orchestrator Agent:**
        *   **Responsibility:** Manages the lifecycle of refactoring tasks.
        *   **Input:** Prioritized list of refactoring tasks from Triage Agent.
        *   **Tools:** MCP client for your task manager.
        *   **Action:**
            1.  Creates tasks in the external task manager with clear descriptions, context, proposed solutions, and priority.
            2.  Assigns tasks (potentially to a human developer queue or a dedicated "Code Implementer Agent").
            3.  Monitors task status.
    *   **Code Implementer Agent (Optional - Advanced):**
        *   **Responsibility:** Attempts to automatically implement the proposed refactoring.
        *   **Input:** A specific refactoring task with detailed instructions and code snippets.
        *   **Action:**
            1.  Modifies the codebase according to the refactoring plan.
            2.  (Crucially) Runs existing tests or even attempts to generate new tests for the refactored code.
            3.  Commits changes to a new branch for review.
        *   **Challenges:** This is the hardest part to fully automate reliably. Requires robust testing and validation. May start as human-in-the-loop.
        *   **Prompt Focus:** "Apply the following refactoring: Extract the selected lines from `function_A` into a new private method `_helper_B` within the same class. Update `function_A` to call `_helper_B`. Original code: `<code>`. Lines to extract: `<code>`."

*   **E. Learning & Feedback Loop:**
    *   **Quality Assurance (QA) Agent / Review Agent:**
        *   **Responsibility:** Evaluates the quality of implemented refactorings.
        *   **Input:** Code changes (diffs) from implemented tasks.
        *   **Action:**
            1.  Re-runs relevant Pattern Detection Agents on the changed code.
            2.  Checks if the original issue is resolved.
            3.  Checks for new issues introduced by the change.
            4.  If tests exist, verifies they pass.
        *   **Prompt Focus:** "Review this code diff. Did it successfully address the 'lack of DRY' issue? Did it introduce any new anti-patterns?"
    *   **Knowledge Base Updater:**
        *   **Responsibility:** Updates the system's knowledge based on outcomes.
        *   **Input:** Feedback from QA Agent, successful/failed refactoring attempts.
        *   **Action:**
            1.  Refines prompts or heuristics for Pattern Detection Agents if they missed something or had false positives.
            2.  Learns which refactoring strategies are more successful for certain patterns.

**3. Workflow (using LangGraph State Machine)**

1.  **Initialization:** Codebase Monitor detects changes.
2.  **Parsing & Indexing:** Code Parser/Indexer updates knowledge bases (VectorDB, GraphDB, ASTs).
3.  **Architectural Analysis:** Architectural Analyst updates its understanding of the system.
4.  **Issue Identification Loop (Iterate per module/file or focus area):**
    *   Pattern Detection Agents scan code, referencing architectural context.
    *   Identified issues are collected.
5.  **Solution Proposal:** Refactoring Strategist generates solutions for identified issues.
6.  **Triage & Prioritization:** Triage Agent prioritizes proposed solutions.
7.  **Task Creation:** Task Orchestrator creates tasks in the external task manager.
8.  **(Manual/Automated) Implementation:**
    *   If manual: Human developer picks up task.
    *   If automated: Code Implementer Agent attempts refactoring.
9.  **Verification & Feedback:**
    *   Implemented changes are committed (e.g., to a PR).
    *   Codebase Monitor detects these new changes, triggering a focused re-analysis by the QA Agent.
    *   QA Agent reports success/failure/new issues.
    *   Knowledge Base Updater learns from the outcome.
10. **Cycle:** The system continuously monitors and repeats.

**4. LangGraph State & Transitions:**

*   **State Object:** Could include:
    *   `current_codebase_snapshot_id`
    *   `files_to_analyze` (list of modified files)
    *   `parsed_code_artifacts` (paths to ASTs, indexed data references)
    *   `architectural_model`
    *   `identified_issues` (list of dicts: {issue_type, location, description, code_snippet})
    *   `proposed_solutions` (list of dicts: {issue_id, solution_description, proposed_code_changes})
    *   `prioritized_tasks` (list of dicts: {solution_id, priority, task_manager_id})
    *   `active_branch_for_refactoring` (if Code Implementer Agent is used)
*   **Nodes:** Each agent (or a logical group of agent actions) can be a node in LangGraph.
*   **Edges:** Conditional transitions based on the output of agents (e.g., if issues found, go to Refactoring Strategist; if no issues, wait for new code changes).

**5. Research Areas & Tasks**

*   **RA1: Code Representation & Understanding**
    *   T1.1: Implement Git integration for codebase monitoring.
    *   T1.2: Research and select optimal AST parsing libraries for target language(s).
    *   T1.3: Develop robust code chunking strategies for effective LLM context and vector embedding.
    *   T1.4: Set up and design schema for Vector Database (e.g., ChromaDB) for semantic search of code and documentation.
    *   T1.5 (Optional): Design schema and set up Graph Database (e.g., Neo4j) for structural relationships.
    *   T1.6: Develop prompts for the Architectural Analyst Agent to summarize module responsibilities and map dependencies.

*   **RA2: Pattern & Anti-Pattern Detection**
    *   T2.1: Curate a list of target anti-patterns and best practices (DRY, Test Coverage, Transaction Mgt, Abstraction, etc.).
    *   T2.2: Develop highly specific prompts for LLMs to identify each target pattern. This will involve iterative testing.
    *   T2.3: Integrate existing linters/static analysis tools; develop parsers for their output to be fed to LLMs for interpretation or summary.
    *   T2.4: Research methods for combining symbolic analysis (ASTs, linters) with semantic LLM analysis for higher accuracy.
    *   T2.5: Develop heuristics for Test Coverage Agent (e.g., "public function without a corresponding `test_` function in test files").
    *   T2.6: Design a confidence scoring mechanism for identified issues (LLM can provide this).

*   **RA3: Solution Generation & Refactoring**
    *   T3.1: Develop prompts for Refactoring Strategist Agent to propose solutions for each identified pattern type.
        *   Example: "Given code X with anti-pattern Y, propose 2-3 ways to refactor it, explaining pros/cons."
    *   T3.2: Research techniques for LLMs to generate code diffs or "before/after" examples for refactoring.
    *   T3.3 (Advanced): For Code Implementer Agent, investigate techniques for LLM-driven code modification and validation (e.g., using tools like `aider-chat` as inspiration but integrated into the agent framework).

*   **RA4: Prioritization & Task Management**
    *   T4.1: Define detailed criteria and weighting for the Triage & Prioritization Agent.
    *   T4.2: Develop prompts for the Triage Agent to assess issues against criteria and assign priority.
    *   T4.3: Implement MCP client integration for the Task Orchestrator Agent to create/update tasks in your task manager.

*   **RA5: Agent Framework & Orchestration (LangChain/LangGraph)**
    *   T5.1: Design the overall LangGraph state machine, defining states, agent nodes, and conditional edges.
    *   T5.2: Implement each agent as a LangChain component (Runnable, Tool, etc.).
    *   T5.3: Develop mechanisms for inter-agent communication and context passing.
    *   T5.4: Implement robust error handling and logging within the agent system.

*   **RA6: Evaluation & Feedback Loop**
    *   T6.1: Develop a methodology for evaluating the system's performance (precision/recall of issue detection, quality of proposed solutions).
    *   T6.2: Create a "golden dataset" of code with known issues and desired refactorings for testing.
    *   T6.3: Implement the QA Agent logic for verifying fixes and detecting regressions.
    *   T6.4: Design how the Knowledge Base Updater will refine prompts or heuristics based on feedback.

**6. Tools & Technologies (Recap & Additions)**

*   **Agent Framework:** LangChain, LangGraph.
*   **LLMs:** OpenAI (GPT-4, GPT-3.5-turbo), Anthropic Claude, or open-source models (e.g., Mixtral, Llama) via Ollama/vLLM. GPT-4 or Claude 2/3 are likely needed for strong reasoning.
*   **Programming Language for Agents:** Python.
*   **Code Parsing:** `tree-sitter` (multi-language), Python `ast`.
*   **Vector Database:** ChromaDB, FAISS, Weaviate, Pinecone.
*   **Graph Database (Optional):** Neo4j.
*   **Task Manager:** Your existing system with MCP client.
*   **Version Control:** Git.
*   **Linters/Static Analyzers:** ESLint, Pylint, SonarQube (community edition), Bandit, etc.
*   **Testing:** Pytest (for the agent system itself).

**7. Prioritization Mechanism (Details for Triage Agent)**

1.  **Input:** An identified issue from a Pattern Detection Agent, along with the proposed solution from the Refactoring Strategist.
2.  **LLM-Assisted Assessment:**
    *   **Prompt to Triage Agent:**
        ```
        Context:
        Issue Type: [e.g., Manual DB Transaction Handling]
        File: [path/to/file.py]
        Lines: [line_numbers]
        Code Snippet: ```python ... ```
        Description: [Description of why it's an issue]
        Proposed Solution: [Description of refactoring, e.g., "Wrap in SQLAlchemy session context manager"]
        Architectural Context: [Brief summary of the module's role from Architectural Analyst]

        Task:
        Assess this issue and its proposed solution based on the following criteria. Provide a score (1-5, 5 being highest impact/easiest) and a brief justification for each:
        1. Security Risk (Potential for security vulnerabilities if not fixed):
        2. Data Integrity Risk (Potential for data corruption/loss):
        3. Performance Impact (Is this likely a bottleneck or inefficient?):
        4. Maintainability Impact (How much harder does this make understanding/changing code?):
        5. Testability Impact (Does this hinder writing effective tests?):
        6. Estimated Effort to Fix (1=very high, 5=very low):
        7. Breadth of Impact (How many other parts of the system are affected or could be affected by this or similar patterns?):

        Output:
        A JSON object with scores and justifications for each criterion, and an overall recommended priority (Critical, High, Medium, Low).
        ```
3.  **Scoring & Weighting:**
    *   The Triage Agent (or a subsequent rule-based system) takes the LLM's assessment.
    *   Apply configurable weights to each criterion:
        *   `PriorityScore = (w_sec * score_sec) + (w_data * score_data) + ... + (w_effort * score_effort)`
    *   Define thresholds for Critical, High, Medium, Low based on the PriorityScore.
4.  **Contextual Adjustments:**
    *   Consider the frequency of the anti-pattern across the codebase (from Pattern Detection Agent's aggregate report). High frequency might elevate priority.
    *   Consider project-specific goals (e.g., "current sprint focus is on improving DB stability" -> give higher weight to data integrity issues).
5.  **Output:** A prioritized list of tasks, ready for the Task Orchestrator.

**8. Challenges & Considerations**

*   **Prompt Engineering:** Getting reliable and consistent output from LLMs for code analysis and generation is a significant challenge.
*   **Context Window Limits:** Large codebases or complex files might exceed LLM context windows. Effective chunking and summarization are crucial.
*   **Accuracy & False Positives/Negatives:** The system will not be perfect. Human review will likely be necessary, especially initially.
*   **Cost:** LLM API calls can be expensive for large-scale, continuous analysis. Consider using smaller/local models for some tasks if feasible.
*   **State Management:** Keeping track of the analysis state across a large, evolving codebase is complex. LangGraph will help.
*   **Determinism:** LLM outputs can be non-deterministic. Setting low `temperature` can help, but some variability is expected.
*   **Integration Complexity:** Integrating various tools (parsers, linters, DBs, task manager) requires careful engineering.
*   **Safety of Automated Refactoring:** The Code Implementer Agent is high-risk. It needs extremely robust testing, validation, and probably human oversight before committing changes. Start with generating suggestions and diffs for human review.

**Next Steps (Phased Approach):**

1.  **Phase 1: Foundation & Core Analysis (MVP)**
    *   Set up Code Ingestion (Git, basic parsing, vector DB for one language).
    *   Implement 1-2 Pattern Detection Agents for high-impact, easy-to-define patterns (e.g., manual DB transactions, a simple DRY check).
    *   Basic Refactoring Strategist to suggest textual fixes.
    *   Manual Triage & Task Creation (initially, no Triage Agent or Task Orchestrator).
    *   Focus on getting the core LangChain/LangGraph loop working for this small scope.
2.  **Phase 2: Expanding Detection & Suggestion**
    *   Add more Pattern Detection Agents.
    *   Improve Architectural Analyst capabilities.
    *   Enhance Refactoring Strategist to propose more complex changes and code snippets.
    *   Develop the Triage & Prioritization Agent.
    *   Integrate the Task Orchestrator with your MCP client.
3.  **Phase 3: Automation & Refinement**
    *   Experiment with the Code Implementer Agent (start with very simple, safe refactorings).
    *   Implement the QA Agent and feedback loop.
    *   Optimize prompts, performance, and cost.
    *   Expand language support if needed.
4.  **Phase 4: Advanced Features & Learning**
    *   Incorporate graph database for deeper structural analysis.
    *   More sophisticated learning mechanisms in the Knowledge Base Updater.
    *   Explore using agents to generate tests for refactored code.

This plan provides a comprehensive roadmap. It's a significant undertaking, so breaking it into manageable phases and iterating will be key to success. Good luck!
```




## Project Decomposition

### Code Ingestion

Lets start with Code Injestion. Lets assume we want to work on an existing code base and identify areas of opportunities - we're not going to target reading pull requests or git commits.

Lets assume in this MVP that we'll be targeting a Javascript or Typescript project, specfically a basic CRUD API - so only backend.

To decompose the code base, we will have a tool or MCP server that can access the LSP of the language (Javascript/Typescript). We may need to write some code to interact with it.

I assume we'll want to extract some or all of the code within the project. Lets figure out how we want to break up that code. We'll probably want to attach metadata to each of the chunks - it would probably have a git commit sha, the file name, and line number range, but there may be additional information to capture. We may want to pass each chunk through a small model that will identify a summary of what the code does, maybe classify in some way (logic, database, external api call, etc (This list needs to be improved on)). Is there additional information that can be captured or added??

Once the code is extracted and tagged?? (What's a good term for adding the metadata to the code chunks?), it sounds like it needs to be indexed - or put into one or more databases - a vector database, maybe a graph database, and probably some keyword search tool so we can later use BM25 ranking.

```
    Okay, let's dive deep into the Code Ingestion phase for your Javascript/Typescript CRUD API backend project. This is the foundation upon which all subsequent analysis will be built, so getting it right is crucial.

    **Goal of Code Ingestion:** To transform the raw source code of an existing application into a structured, enriched, and indexed representation that is readily analyzable by AI agents.

    **Assumptions for MVP:**

    *   **Target:** Existing Javascript/Typescript backend codebase (CRUD API).
    *   **Scope:** No real-time monitoring (PRs/commits); analysis of a static snapshot.
    *   **LSP Access:** A tool/MCP server can provide LSP-like information (or we use direct parsing).

    **Core Terminology:**

    *   **Chunk:** A semantically meaningful segment of code (e.g., function, class, method).
    *   **Augmentation:** The process of adding metadata, summaries, classifications, and other relevant information to code chunks.
    *   **Indexed Representation:** Storing augmented chunks in databases optimized for different types of queries (semantic, keyword, graph-based).

    ---

    **Detailed Breakdown of the Code Ingestion Process:**

    **Phase 1: Code Acquisition & Initial Parsing**

    1.  **Input:** Path to the root directory of the JS/TS project.
    2.  **File Discovery:**
        *   **Task:** Recursively scan the project directory for relevant source files.
        *   **Details:**
            *   Target extensions: `.ts`, `.tsx`, `.js`, `.jsx`.
            *   Consider including `.json` (e.g., `package.json` for dependencies, configuration files).
            *   Optionally exclude `node_modules`, `dist`, `build` directories, test files (or flag them differently).
        *   **Tools:** Standard file system libraries in Python (e.g., `os.walk`, `pathlib`).
    3.  **Obtain Commit SHA:**
        *   **Task:** Get the current Git commit SHA of the codebase being analyzed.
        *   **Details:** This provides a version identifier for the snapshot.
        *   **Tools:** `git rev-parse HEAD` executed via `subprocess` module.
    4.  **Per-File Parsing (AST Generation):**
        *   **Task:** For each identified source file, parse it into an Abstract Syntax Tree (AST).
        *   **Details:**
            *   **For TypeScript/JavaScript:** The **TypeScript Compiler API** is the most robust choice. It can parse `.ts`, `.tsx`, `.js`, `.jsx` and provide rich type information and AST nodes.
                *   Key functionalities: `ts.createSourceFile`, `ts.forEachChild` for traversal.
            *   **Alternative/Complement:** `tree-sitter` with `tree-sitter-javascript` and `tree-sitter-typescript` grammars. `tree-sitter` is excellent for purely syntactic parsing and is language-agnostic if you plan to expand.
            *   **LSP Interaction (if primary):** If your MCP server exposes LSP functions like `textDocument/documentSymbol` or `textDocument/semanticTokens`, this can give you structured information. However, direct AST parsing often gives more granular control for chunking. LSP is powerful for *cross-file* understanding (find references, go to definition), which will be more useful in later analysis agents. For initial chunking within a file, AST is king.
        *   **Output:** An AST object for each file.

    **Phase 2: Code Chunking**

    1.  **Goal:** Divide the code within each file into meaningful, manageable units (chunks).
    2.  **Chunking Strategy (prioritized):**
        *   **Primary Units:**
            *   Functions (top-level functions, arrow functions assigned to variables)
            *   Methods (within classes)
            *   Classes (as a whole, can also be a "container" chunk for its methods)
        *   **Secondary/Optional Units (for deeper analysis later):**
            *   Top-level import/export statements.
            *   Significant blocks (e.g., large `try-catch` blocks, complex conditional blocks if they represent distinct logic units – might be too granular for MVP).
        *   **Implementation:** Traverse the AST. Identify nodes corresponding to functions (`FunctionDeclaration`, `ArrowFunction`, `MethodDeclaration`), classes (`ClassDeclaration`).
    3.  **Chunk Definition:**
        *   **Content:** The raw source code text of the function/method/class.
        *   **Initial Metadata (from AST):**
            *   `chunk_id`: A unique identifier for this chunk (e.g., UUID).
            *   `file_path`: Absolute or relative path to the source file.
            *   `start_line`, `end_line`: Line numbers in the original file.
            *   `start_char`, `end_char`: Character offsets in the original file.
            *   `chunk_type`: e.g., "function", "method", "class", "arrow_function".
            *   `name`: Name of the function, method, or class. (Handle anonymous functions appropriately, perhaps using a parent context or generated name).
            *   `parent_name`: If a method, the name of the class. If a nested function, the name of the outer function.
            *   `parameters`: List of parameter names (and types if available from TS).
            *   `return_type`: (If available from TS).
            *   `docstring_jsdoc`: Extracted JSDoc comments associated with the node.

    **Phase 3: Chunk Augmentation (Adding Rich Metadata)**

    This is where we add layers of understanding to each chunk.

    1.  **Basic Metadata (already captured or easily derived):**
        *   `commit_sha`: (From Phase 1) Apply to all chunks from this snapshot.
        *   `language`: "typescript" or "javascript".
        *   `chunk_LOC`: Lines of code within the chunk itself.
    2.  **Syntactic/Structural Metadata (from AST/LSP):**
        *   **Internal Calls:** List of other functions/methods called *within* this chunk that are defined *within the same project*. (AST traversal or LSP `textDocument/references`).
        *   **External Calls/Library Usage:** List of functions/methods called that belong to external libraries/modules (identified from import statements and call expressions).
        *   **Variables Declared/Modified:** (Can be complex, but useful for data flow).
        *   **Cyclomatic Complexity:** Calculated from the AST. (Tools like `escomplex` or custom AST traversal logic).
    3.  **LLM-Powered Augmentation (per chunk):**
        *   **Task:** Pass the raw code of each chunk (and potentially its immediate context like class name or JSDoc) to an LLM.
        *   **Tool:** LangChain to manage LLM calls, prompts, and output parsing.
        *   **Prompts & Desired Outputs:**
            *   **a. Plain Language Summary:**
                *   **Prompt:** "Provide a concise, one-sentence summary of what this TypeScript code snippet does: `\n{code_snippet}\n` If it interacts with a database or external API, mention that."
                *   **Output:** `summary_text: "Handles user registration by validating input and saving data to the database."`
            *   **b. Functional Classification:**
                *   **Categories (CRUD API focus, expandable):**
                    1.  `ROUTER_HANDLER`: (e.g., Express.js route definitions, initial request/response handling)
                    2.  `INPUT_VALIDATION`: (Code primarily focused on validating request data)
                    3.  `BUSINESS_LOGIC_SERVICE`: (Core application logic, orchestrating operations, not direct DB/API calls but calling those who do)
                    4.  `DATABASE_INTERACTION_QUERY`: (Direct database queries, ORM calls like Prisma/TypeORM/Sequelize)
                    5.  `DATABASE_INTERACTION_SETUP`: (Migrations, schema definitions, connection setup - less common in chunks, more file-level)
                    6.  `EXTERNAL_API_CLIENT`: (Code making HTTP requests to third-party services)
                    7.  `AUTHENTICATION_AUTHORIZATION`: (Handling logins, checking permissions, token management)
                    8.  `DATA_TRANSFORMATION_MAPPING`: (DTOs, mapping between data models, serialization)
                    9.  `UTILITY_HELPER`: (Generic reusable functions, e.g., string manipulation, date formatting)
                    10. `ERROR_HANDLING_CUSTOM`: (Custom error classes, dedicated error handling middleware/functions)
                    11. `CONFIGURATION_SETUP`: (Reading/parsing config files, setting up app-level configs)
                    12. `MIDDLEWARE`: (Express.js or similar middleware functions)
                    13. `FILE_SYSTEM_IO`: (Reading/writing files, if applicable)
                    14. `OTHER`: (If none of the above fit well)
                *   **Prompt:** "Classify the primary functional purpose of this TypeScript code snippet: `\n{code_snippet}\n` Choose one primary category from the following list: [list categories]. Provide a brief justification. If relevant, list one or two secondary categories. Output in JSON format: `{ \"primary_category\": \"X\", \"secondary_categories\": [\"Y\"], \"justification\": \"...\" }`"
                *   **Output:** `classification: { "primary_category": "DATABASE_INTERACTION_QUERY", "secondary_categories": ["BUSINESS_LOGIC_SERVICE"], "justification": "The code directly uses Prisma client to fetch user data and involves some logic to filter results." }`
            *   **c. Identifying Key Entities/Concepts:**
                *   **Prompt:** "Identify the key business entities or concepts (e.g., 'User', 'Order', 'Payment') primarily manipulated or referenced in this TypeScript code snippet: `\n{code_snippet}\n` Output a JSON list of strings."
                *   **Output:** `key_entities: ["User", "Profile"]`
            *   **d. Potential Anti-patterns (Lightweight Initial Pass - more detailed later):**
                *   **Prompt:** "Does this code snippet: `\n{code_snippet}\n` exhibit any obvious signs of common issues like excessively long function, deeply nested logic, or missing error handling for critical operations? Briefly state observations. This is a preliminary check."
                *   **Output:** `preliminary_flags: ["Function appears long, consider splitting.", "No explicit try-catch around database call."]` (This is a teaser for the more detailed analysis agents).

    4.  **Consolidate Metadata:** Combine all gathered metadata (from AST, LLM, etc.) into a single structured object for each chunk.

    **Phase 4: Data Storage & Indexing**

    1.  **Goal:** Store the augmented code chunks in a way that supports efficient querying for different analysis tasks.
    2.  **Databases/Indexing Mechanisms:**
        *   **a. Vector Database (e.g., ChromaDB, Weaviate, Pinecone, FAISS with a wrapper):**
            *   **Purpose:** Semantic search ("find code that performs user authentication," "find code similar to this problematic snippet").
            *   **What to Embed:**
                *   The raw code of the chunk.
                *   The LLM-generated `summary_text`.
                *   (Optional) JSDoc/docstring.
            *   **Embedding Model:** Sentence Transformers (e.g., `all-MiniLM-L6-v2`), OpenAI Embeddings API, Cohere Embed, etc.
            *   **Metadata Storage:** Most vector DBs allow storing arbitrary metadata alongside the vectors. Store *all* the augmented metadata here (file_path, line numbers, classification, summary, entities, commit_sha, etc.). This makes the vector DB a primary query point.
            *   **Tools:** `chromadb`, `weaviate-client`, `pinecone-client` Python libraries.
        *   **b. Graph Database (e.g., Neo4j, Memgraph - highly recommended for architectural analysis):**
            *   **Purpose:** Model relationships between code elements for understanding dependencies, call graphs, and impact analysis.
            *   **Node Types:**
                *   `File` (properties: path, commit_sha)
                *   `Chunk` (properties: chunk_id, name, type, start_line, end_line, summary, classification, direct link/ID to vector DB entry)
                *   `Class` (if chunking at class level, or as a special Chunk type)
                *   `ExternalLibrary` (properties: name)
            *   **Relationship Types:**
                *   `(Chunk)-[:DEFINED_IN_FILE]->(File)`
                *   `(Class)-[:CONTAINS_METHOD]->(Chunk where chunk_type='method')`
                *   `(Chunk)-[:CALLS_INTERNAL]->(Chunk)` (derived from `internal_calls` metadata)
                *   `(Chunk)-[:USES_LIBRARY_FUNCTION {function_name: 'xyz'}]->(ExternalLibrary)`
                *   `(File)-[:IMPORTS_LIBRARY]->(ExternalLibrary)`
            *   **Tools:** `neo4j` Python driver, `py2neo`.
            *   **Process:** After chunks are augmented, iterate through them and their `internal_calls` / `external_calls` metadata to create nodes and relationships in the graph DB.
        *   **c. Keyword Search / Full-Text Search (BM25):**
            *   **Purpose:** Traditional keyword searching (e.g., find all occurrences of "processPayment").
            *   **Implementation Options:**
                *   Many modern Vector DBs (like Weaviate, some configurations of Vespa) offer hybrid search (BM25 + vector search). This is often the easiest.
                *   Elasticsearch/OpenSearch: If you need very advanced full-text search capabilities. Requires separate indexing.
                *   Simpler BM25 libraries in Python (e.g., `rank_bm25`) if you manage your own document store (could be a simple JSONL file or a relational DB for metadata if not fully in VectorDB).
            *   **What to Index:** Raw code, summaries, JSDoc, function/class names.
            *   **Recommendation for MVP:** Leverage hybrid search in your chosen Vector DB if available. Otherwise, focus on Vector DB for now and add sophisticated keyword search later if needed.

    **Process Flow Summary for Ingestion:**

    ```mermaid
    graph TD
        A[Start: Project Directory Path] --> B{Scan for JS/TS Files};
        B --> C[Get Git Commit SHA];
        B -- For Each File --> D{Parse File (TS Compiler API/tree-sitter)};
        D -- AST --> E{Extract Chunks (Functions, Classes, Methods)};
        E -- For Each Chunk --> F[Gather Basic Metadata (Path, Lines, Name)];
        F --> G{Augment with LLM (Summary, Classification, Entities)};
        G --> H{Augment with AST/Static Analysis (Complexity, Calls)};
        H --> I[Consolidate All Chunk Metadata];
        I --> J{Store & Index};
        J -- Embeddings & Metadata --> K[Vector Database (ChromaDB, Weaviate)];
        J -- Nodes & Relationships --> L[Graph Database (Neo4j)];
        J -- Text for Keyword Search --> M[Keyword Index (e.g., via VectorDB Hybrid Search)];
        K --> Z[Indexed Codebase Ready];
        L --> Z;
        M --> Z;
    ```

    **What else might be missing or needs consideration?**

    1.  **Configuration Management:**
        *   How to specify include/exclude paths, LLM models, API keys, database connection details.
        *   A configuration file (`config.yaml` or similar) for the ingestion agent.
    2.  **Error Handling & Logging:**
        *   Robust error handling (e.g., file parsing errors, LLM API failures).
        *   Detailed logging of the ingestion process.
    3.  **Idempotency/Caching:**
        *   For MVP, re-processing all files on each run is acceptable for a static snapshot.
        *   Later, consider caching ASTs or LLM results for unchanged files (based on file hashes or commit SHAs) to speed up re-runs.
    4.  **Scalability for Very Large Projects:**
        *   LLM calls can be time-consuming and costly. Batching requests, asynchronous processing.
        *   Efficient AST traversal and chunking.
        *   For now, assume project size is manageable for single-threaded or simple concurrent processing.
    5.  **Handling Minified/Obfuscated Code:**
        *   This process assumes source code. If you encounter minified bundles, analysis quality will be very low. This should be filtered out or flagged.
    6.  **Type Information Depth (TypeScript):**
        *   The TypeScript Compiler API can provide very rich type information. Decide how much of this to extract and store. Full type resolution can be computationally intensive but highly valuable for certain analyses (e.g., precise data flow). Start with names and basic types, expand as needed.
    7.  **Incremental Updates (Post-MVP):**
        *   When moving to monitor PRs/commits, the ingestion process will need to handle deltas efficiently, updating only affected chunks and their relationships. This involves comparing new ASTs with cached ones.

    This detailed plan for Code Ingestion should provide a solid foundation for your CodeGuardian AI system. The augmented and indexed representation will be a rich dataset for your subsequent analysis agents to work with.
```

### Thoughts

* Inputs:
  * Root Project directory
  * Target files - may just default this for a particular language
    * May also want to include `json`
  * `.gitignore` file to apply to file filtering

* Need a module that will be able to interact with git, specifically get the sha within a specific working directory (root project directory)
* Search through project directory to identify all files involved
  * May need to ensure filtering is implemented - like use the `.gitignore` to remove `node_modules`, etc
* Need a language speficic module that will capture the AST
  * Whats the tool that's used by Typescript to output the AST?

#### Graph Database: Alternatives for Neo4J

All database access should be on-machine and probably be stored within the project (in a root 'dot' folder).

The following are two Graph Databse alternatives to Neo4J that work similar to SQLite - meaning they support local persistence.

This process will resemble OLAP or analytical workflows.

1.  **KùzuDB:**
    *   **Model:** Property Graph (like Neo4j).
    *   **Query Language:** Cypher (specifically openCypher, which is very close to Neo4j's Cypher).
    *   **SQLite-like:** Yes. It's an embeddable, file-based graph database. You interact with it via a library in your application (Python, C++, Java, Node.js, Rust). The database is stored as a directory of files.
    *   **Focus:** Optimized for OLAP (analytical) workloads on graphs, but also supports OLTP (transactional) updates.
    *   **License:** Permissive (MIT).
    *   **Status:** Actively developed and gaining traction. This is probably the *closest* modern equivalent to what you're asking for if you want a Neo4j-like experience.

2.  **Oxigraph:**
    *   **Model:** RDF (Resource Description Framework) Quad/Triple Store. This is a W3C standard graph model, different from Neo4j's Labeled Property Graph (LPG) model but very powerful.
    *   **Query Language:** SPARQL (the standard query language for RDF).
    *   **SQLite-like:** Yes. It can be embedded as a library (Rust, Python, JavaScript/WASM) and store its data in a single file (using RocksDB or Sled as a backend) or in memory.
    *   **Focus:** High-performance, spec-compliant RDF database.
    *   **License:** Permissive (MIT / Apache 2.0).
    *   **Status:** Mature and well-regarded in the RDF space.



