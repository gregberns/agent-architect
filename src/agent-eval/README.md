# Agent Evaluation and Evolution System

## Overview

This system implements an iterative agent development process with two primary phases: **Epoch Evaluation** and **Epoch Evolution**. The goal is to continuously improve an AI agent's coding capabilities through systematic testing and self-improvement cycles.

## System Lifecycle

### Phase 1: Epoch Evaluation
**Purpose**: Test agent capabilities against standardized programming tasks

**Process**:
1.  **Task Execution**: The evaluation script runs the agent through standard programming tasks in parallel.
2.  **Code Generation**: The agent produces source code and logs for each task.
3.  **Validation**: The system automatically runs compilation checks and tests on the generated code.
4.  **Scoring**: A simple point system is used per task:
    - 1 point: Task execution completes successfully.
    - 1 point: Generated code compiles.
    - 1 point: Generated code passes all tests.
5.  **Metrics Generation**: Scores are aggregated to generate an epoch performance summary.

### Phase 2: Epoch Evolution (Future)
**Purpose**: Create new improved agent versions through self-modification

**Process**:
1.  **Epoch Selection**: Choose a source epoch (e.g., epoch-001).
2.  **Self-Improvement**: The agent in a new epoch analyzes and improves its own code based on the performance data from the previous evaluation.
3.  **New Cycle**: Trigger the evaluation phase on the new, evolved epoch.

## Directory Structure

```
src/agent-eval/
├── epochs/
│   ├── epoch-001/
│   │   ├── agent-src/              # Agent implementation for this epoch
│   │   ├── runs/                   # Evaluation run results for each task
│   │   └── metrics/                # Aggregate scores and performance data
│   └── ...
├── default-workspaces/             # Template tasks copied to each epoch
│   ├── task-001/
│   └── ...
├── orchestrator/                   # Scripts to run evaluations
│   ├── evaluate_epoch.py         # Main script to run an epoch evaluation
│   └── config.json               # Parallelism and timeout config
└── evaluation/                    # Testing and validation framework
    └── metrics-collectors/
```

## Core Components

### 1. Epoch-Based Agent Code
- Each epoch contains a complete, Dockerized agent implementation in `agent-src/`.

### 2. Standardized Task System
- **Default Workspaces**: Template programming tasks that remain consistent across evaluations.
- **Task Structure**: `input/TASK.md`, `expected-output/`, and `tests/`.

### 3. Evaluation Framework
- **Parallel Execution**: The `evaluate_epoch.py` script manages parallel execution of tasks using a process pool.
- **Automated Validation**: Code is automatically compiled and tested in an isolated environment.
- **Scoring System**: A 3-point system tracks task completion, compilation, and test success.
- **Metrics Collection**: Performance is tracked and reported across epochs.

### 4. Evolution Mechanism (Future)
- The system is designed to support a future evolution phase where agents modify their own code based on performance feedback.

## Orchestration and Execution

The orchestration system has been simplified to a single script. There is no longer a need for a persistent orchestrator daemon or a file-based job queue.

### Running an Evaluation

To run a full evaluation for an epoch, use the `evaluate_epoch.py` script. It handles task setup, parallel execution, validation, and metrics generation in one go.

```bash
# Run a full evaluation for epoch-001
python3 orchestrator/evaluate_epoch.py --epoch epoch-001
```

The script will provide live progress updates as tasks are completed or fail.

### Configuration

System behavior, such as the number of parallel processes and timeouts, is configured in `orchestrator/config.json`:

```json
{
  "parallelism": {
    "max_concurrent_jobs": 5
  },
  "timeouts": {
    "task_execution_timeout": 300,
    "validation_timeout": 120
  }
}
```

## Next Steps Priority

With the new simplified and reliable evaluation system, the focus can now shift to the Evolution System.

### Phase 1: Evolution System
1.  **Design `evolve-epoch.py`**: Create a script to manage the self-improvement process, likely using a similar parallel execution pattern.
2.  **Implement Evolution Agent Logic**: The agent needs prompts and tools to analyze its own code and performance reports to suggest improvements.
3.  **Integrate Feedback Loop**: Connect the output of the evaluation phase (metrics, reports) as input to the evolution phase.

## Success Criteria

- **Automated Evaluation**: Full epoch evaluation runs without manual intervention via a single command.
- **Code Validation**: Generated code executes and passes tests reliably.
- **Evolution Capability**: Agent can improve its own codebase (Next Phase).
- **Performance Tracking**: Clear metrics show improvement over time.
- **Scalability**: System handles multiple tasks concurrently in a stable manner.
