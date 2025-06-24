# Agent Evaluation and Evolution System

## Overview

This system implements an iterative agent development process with two primary phases: **Epoch Evaluation** and **Epoch Evolution**. The goal is to continuously improve an AI agent's coding capabilities through systematic testing and self-improvement cycles.

## System Lifecycle

### Phase 1: Epoch Evaluation
**Purpose**: Test agent capabilities against standardized programming tasks

**Process**:
1. **Task Execution**: Agent runs through standard programming tasks
2. **Code Generation**: Agent produces source code and logs for each task
3. **Compilation Check**: Execute generated code to verify it compiles/runs
4. **Test Execution**: Run tests to validate correctness
5. **Scoring**: Simple point system per task:
   - 1 point: Code compiles and runs successfully
   - 1 point: Tests pass successfully
6. **Metrics Generation**: Aggregate scores and generate epoch performance summary

### Phase 2: Epoch Evolution
**Purpose**: Create new improved agent versions through self-modification

**Process**:
1. **Epoch Selection**: Choose a source epoch (e.g., epoch-001)
2. **Multi-Branch Creation**: Generate multiple new epochs (e.g., epoch-002, epoch-003, epoch-004)
3. **Code Seeding**: Copy source epoch's agent-src to new epochs' agent-src directories
4. **Evolution Task Setup**: Copy source epoch's code into workspace/task folders within new epochs
5. **Self-Improvement**: Each new epoch's agent analyzes and improves its own code
6. **New Cycle**: Trigger evaluation phase on new epochs

## Directory Structure

```
src/agent-eval/
├── epochs/
│   ├── epoch-001/
│   │   ├── agent-src/              # Agent implementation for this epoch
│   │   │   ├── Dockerfile
│   │   │   ├── docker-compose.yml
│   │   │   ├── agent.py
│   │   │   └── requirements.txt
│   │   ├── runs/                   # Evaluation run results
│   │   │   ├── task-001/
│   │   │   │   ├── input/TASK.md
│   │   │   │   └── output/         # Generated code and logs
│   │   │   ├── task-002/
│   │   │   └── ...
│   │   ├── compilation-check/      # Code execution validation results
│   │   ├── metrics/               # Aggregate scores and performance data
│   │   └── evolution-workspace/   # Workspace for evolution tasks
│   │       └── task-001/          # Contains parent epoch code for improvement
│   ├── epoch-002/
│   │   ├── agent-src/
│   │   ├── runs/
│   │   ├── compilation-check/
│   │   ├── metrics/
│   │   └── evolution-workspace/
│   └── ...
├── default-workspaces/            # Template tasks copied to each epoch
│   ├── task-001/
│   │   ├── input/TASK.md
│   │   └── expected-output/       # For validation
│   ├── task-002/
│   └── ...
├── orchestrator/                  # Job queue and management scripts
│   ├── orchestrator.py           # Main job queue manager
│   ├── evaluate-epoch.py         # Enqueue epoch evaluation jobs
│   ├── evolve-epoch.py           # Enqueue epoch evolution jobs
│   ├── job_queue.py              # Job queue implementation
│   ├── config.py                 # Parallelism and rate limiting config
│   └── workers/                  # Job execution workers
│       ├── task-worker.py        # Execute single task evaluation
│       ├── evolution-worker.py   # Handle epoch evolution
│       └── validation-worker.py  # Run compilation checks
└── evaluation/                   # Testing and validation framework
    ├── test-runners/
    ├── validators/
    └── metrics-collectors/
```

## Core Components

### 1. Epoch-Based Agent Code
- Each epoch contains a complete agent implementation in `agent-src/`
- Dockerized Python application with OpenAI-compatible API interface
- Supports function calling for file operations
- Versioned and isolated per epoch

### 2. Standardized Task System
- **Default Workspaces**: Template programming tasks that remain consistent
- **Task Structure**: 
  - `input/TASK.md` - Problem statement
  - `expected-output/` - Validation criteria
  - Generated `output/` - Agent solutions and logs

### 3. Evaluation Framework
- **Compilation Check**: Automated code execution and validation
- **Scoring System**: Binary points for compilation and test success
- **Metrics Collection**: Performance tracking across epochs

### 4. Evolution Mechanism
- **Multi-Branch Evolution**: Generate multiple candidate improvements
- **Self-Improvement**: Agent modifies its own codebase
- **Workspace Isolation**: Evolution tasks run in dedicated workspace

## Implementation Requirements

### Implemented ✅
- [x] Basic agent architecture with function calling
- [x] Docker containerization with proper layering
- [x] Dynamic task workspace mounting
- [x] Task execution from TASK.md files
- [x] Log capture to task output directories

### Missing Components ❌

#### 1. Job Queue Orchestration System
- **Job Types**:
  - `evaluate_task`: Execute single task within epoch
  - `evolve_epoch`: Generate new epoch from parent
  - `compile_check`: Validate generated code
  - `generate_metrics`: Aggregate results
- **Queue Management**:
  - **Configurable Parallelism**: Control concurrent job execution (e.g., 3-5 simultaneous tasks)
  - **Rate Limiting Protection**: Prevent API throttling with delays/backoff
  - **Retry Logic**: Automatic retry with exponential backoff for transient failures
  - **Job Persistence**: Queue state survives orchestrator restarts
  - **Progress Tracking**: Monitor job status and completion rates

#### 2. Orchestration Scripts
- **orchestrator.py**: Main job queue manager
  - Enqueue/dequeue jobs
  - Monitor worker processes
  - Handle retries and failures
  - Provide status dashboard
- **evaluate-epoch.py**: 
  - Enqueue individual task evaluation jobs
  - Monitor completion and collect results
- **evolve-epoch.py**:
  - Enqueue evolution jobs for multiple new epochs
  - Setup workspace isolation per evolution
- **workers/**:
  - **task-worker.py**: Execute single task evaluation
  - **evolution-worker.py**: Handle epoch evolution tasks
  - **validation-worker.py**: Run compilation checks

#### 2. Evaluation Infrastructure
- Code execution sandbox
- Test framework integration
- Results aggregation system
- Performance comparison tools

#### 3. Task Management
- Default workspace templates
- Task validation criteria
- Expected output definitions
- Test case specifications

#### 4. Evolution Templates
- Self-improvement task instructions
- Code analysis prompts
- Improvement guidelines
- Safety constraints

## Scoring System

**Per Task (Max 2 points)**:
- **Compilation/Execution** (1 point): Generated code runs without errors
- **Test Validation** (1 point): Code passes defined test cases

**Per Epoch**:
- **Total Score**: Sum of all task scores
- **Success Rate**: Percentage of tasks with full points
- **Improvement Delta**: Score difference from parent epoch

## Job Queue Architecture

### Job Types and Flow
```
Epoch Evaluation:
  evaluate-epoch.py → enqueue → [task-001, task-002, ...] → workers → results

Epoch Evolution:
  evolve-epoch.py → enqueue → [epoch-002, epoch-003, epoch-004] → workers → new epochs

Validation:
  compile-check → enqueue → [validate-task-001, validate-task-002] → workers → scores
```

### Configuration
```yaml
# orchestrator/config.yaml
parallelism:
  max_concurrent_jobs: 5
  task_evaluation_workers: 3
  evolution_workers: 2
  
rate_limiting:
  api_requests_per_minute: 20
  retry_backoff_seconds: [1, 2, 4, 8, 16]
  max_retries: 5

timeouts:
  task_execution_timeout: 300  # 5 minutes
  evolution_timeout: 1800      # 30 minutes
```

## Orchestrator Commands

```bash
# Start the job queue orchestrator (background daemon)
python orchestrator/orchestrator.py --start

# Enqueue epoch evaluation (creates multiple task jobs)
python orchestrator/evaluate-epoch.py --epoch epoch-001 --parallel

# Enqueue epoch evolution (creates multiple evolution jobs)
python orchestrator/evolve-epoch.py --source epoch-001 --count 3 --parallel

# Monitor job queue status
python orchestrator/orchestrator.py --status

# Process specific job types
python orchestrator/orchestrator.py --workers task_evaluation=3 evolution=2

# Manual job management
python orchestrator/orchestrator.py --retry-failed
python orchestrator/orchestrator.py --clear-queue
```

## Next Steps Priority

### Phase 1: Basic Structure
1. **Move current agent-src to epochs/epoch-001/**
2. **Create default-workspaces with standard programming tasks**
3. **Implement basic job queue system (job_queue.py)**

### Phase 2: Core Orchestration
4. **Build orchestrator.py with worker management**
5. **Implement task-worker.py for single task execution**
6. **Create evaluate-epoch.py with job enqueueing**
7. **Add validation-worker.py for compilation checks**

### Phase 3: Evolution System
8. **Build evolution-worker.py for epoch evolution**
9. **Create evolve-epoch.py with multi-branch job creation**
10. **Implement metrics collection and aggregation**

### Phase 4: Production Features
11. **Add rate limiting and retry logic**
12. **Create monitoring dashboard**
13. **Add job persistence and recovery**
14. **Performance optimization and tuning**

## Success Criteria

- **Automated Evaluation**: Full epoch evaluation runs without manual intervention
- **Code Validation**: Generated code executes and passes tests reliably
- **Evolution Capability**: Agent can improve its own codebase
- **Performance Tracking**: Clear metrics show improvement over time
- **Scalability**: System handles multiple epochs and evolution branches