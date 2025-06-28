# Agent Evaluation System - Operations Guide

This guide provides step-by-step instructions for operating the refactored agent evaluation system. The system has been simplified to be more reliable and easier to use.

## Table of Contents
1. [System Overview](#system-overview)
2. [Directory Structure](#directory-structure)
3. [Prerequisites](#prerequisites)
4. [Quick Start Guide](#quick-start-guide)
5. [Running Evaluations](#running-evaluations)
6. [Data Flow and Storage](#data-flow-and-storage)
7. [Troubleshooting](#troubleshooting)
8. [Metrics and Reports](#metrics-and-reports)
9. [Cleanup and Maintenance](#cleanup-and-maintenance)

## System Overview

The Agent Evaluation System is designed to:
- Evaluate AI agents against programming tasks in a parallel, automated fashion.
- Track performance across epochs (agent versions).
- Generate metrics and reports for analysis.

**Key Changes:**
The old system based on a persistent daemon (`orchestrator.py`) and a file-based job queue has been **removed**. The new system uses a single script, `evaluate_epoch.py`, which manages the entire evaluation process, making it more reliable and easier to debug.

## Directory Structure

```
src/agent-eval/
├── orchestrator/                    # Core orchestration scripts
│   ├── config.json                 # System configuration
│   └── evaluate_epoch.py           # Main script to run an evaluation
├── epochs/                        # Agent versions storage
│   └── epoch-001/                 # Example epoch
│       ├── agent-src/             # Agent source code
│       ├── runs/                  # Task execution results
│       └── metrics/               # Performance reports
├── default-workspaces/            # Template tasks
└── evaluation/                    # Metrics and analysis tools
```

## Prerequisites

### System Requirements
- Python 3.8+ installed
- Docker and Docker Compose installed

### Environment Setup
```bash
# Navigate to system directory
cd src/agent-eval

# Verify Python installation
python3 --version

# Verify Docker installation
docker --version
docker-compose --version
```

## Quick Start Guide

Running an evaluation is now a single-step process. There is **no need to start or stop a background orchestrator**.

### Run Your First Evaluation
```bash
# Navigate to the orchestrator directory
cd src/agent-eval/orchestrator

# Evaluate epoch-001 against all default tasks
python3 evaluate_epoch.py --epoch epoch-001

# The script will print live progress and a final summary.
# All tasks, validation, and metrics are handled automatically.
```

## Running Evaluations

### Full Epoch Evaluation
The `evaluate_epoch.py` script is the only entry point you need.

```bash
cd src/agent-eval/orchestrator

# Run a standard evaluation
python3 evaluate_epoch.py --epoch epoch-001

# To run an evaluation without generating the final metrics reports
python3 evaluate_epoch.py --epoch epoch-001 --no-metrics
```

The number of parallel processes is controlled by the `max_concurrent_jobs` setting in `config.json`.

### Configuration
You can modify `orchestrator/config.json` to change parallelism and timeouts.

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

## Data Flow and Storage

### Execution Data Flow

1.  **Task Setup**: `evaluate_epoch.py` copies tasks from `default-workspaces/` into `epochs/{epoch}/runs/`.
2.  **Task Execution**: The script runs `docker-compose` for each task in parallel. Agent-generated code and logs are saved to the `output/` directory within each task's `runs` folder.
3.  **Validation**: For each successfully completed task, a validation process is run to compile the code and run `pytest`.
4.  **Metrics Collection**: Results are aggregated, and reports are generated in `epochs/{epoch}/metrics/`.

### Storage Locations

**Task Execution Results:**
```bash
epochs/{epoch}/runs/{task}/output/
```

**Performance Reports:**
```bash
epochs/{epoch}/metrics/
├── evaluation_summary.json         # The detailed summary from the latest run
├── {epoch}_score_report_... .json  # Detailed performance report
└── {epoch}_tasks_... .csv          # Task-level CSV data
```

**Configuration:**
```bash
orchestrator/config.json             # System configuration
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Evaluation fails for a specific task**
- **Solution**: The `evaluate_epoch.py` script will now print an error log snippet for the failed task directly to the console. Check this output to debug the agent's code or the task setup. The full error is in `evaluation_summary.json`.

**Issue: Docker build failures**
- **Solution**: The error from `docker-compose` will be captured and displayed. You can also manually run the build in the agent's source directory to debug:
  ```bash
  cd src/agent-eval/epochs/{epoch}/agent-src
  docker-compose build
  ```

**Issue: All tasks are failing or timing out**
- **Solution**:
    1.  Check that Docker is running correctly (`docker ps`).
    2.  Consider increasing the `task_execution_timeout` in `orchestrator/config.json` if the agent is slow.
    3.  Reduce `max_concurrent_jobs` if your machine is running out of memory or CPU resources.

## Metrics and Reports

Metrics generation is now integrated into the `evaluate_epoch.py` run by default. If you need to regenerate reports or run analysis separately, you can use the `metrics_cli.py` script.

### Generating Reports Manually
```bash
cd src/agent-eval/evaluation/metrics-collectors

# Generate a score summary for an epoch
python3 metrics_cli.py score --epoch epoch-001

# Generate detailed JSON and CSV reports
python3 metrics_cli.py report --epoch epoch-001
```

## Cleanup and Maintenance

### Clean Docker Resources
It's good practice to periodically clean up old Docker containers and images.
```bash
# Remove stopped containers, unused networks, and dangling images
docker system prune -f

# To be more aggressive (removes all unused images, not just dangling ones)
docker system prune -af
```

### System Reset
To reset an epoch's evaluation data, simply delete its `runs/` and `metrics/` directories.
```bash
cd src/agent-eval/epochs/epoch-001

# WARNING: This will delete all results for this epoch.
rm -rf runs/
rm -rf metrics/

# You can now re-run the evaluation for a clean slate.
```
---

## Quick Reference Commands

**The Only Command You Need for Evaluation:**
```bash
# Run a full evaluation for epoch-001
cd src/agent-eval/orchestrator
python3 evaluate_epoch.py --epoch epoch-001
```