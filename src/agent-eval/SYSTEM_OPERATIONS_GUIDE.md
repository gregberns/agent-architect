# Agent Evaluation System - Operations Guide

This guide provides step-by-step instructions for operating the agent evaluation and evolution system manually. Use this document as your reference for running evaluations, managing data, and understanding the complete workflow.

## Table of Contents
1. [System Overview](#system-overview)
2. [Directory Structure](#directory-structure)
3. [Prerequisites](#prerequisites)
4. [Quick Start Guide](#quick-start-guide)
5. [Setting Up New Runs](#setting-up-new-runs)
6. [Running Evaluations](#running-evaluations)
7. [Data Flow and Storage](#data-flow-and-storage)
8. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
9. [Metrics and Reports](#metrics-and-reports)
10. [Manual Operations](#manual-operations)
11. [Cleanup and Maintenance](#cleanup-and-maintenance)

## System Overview

The Agent Evaluation System is designed to:
- Evaluate AI agents against programming tasks
- Track performance across epochs (agent versions)
- Generate metrics and reports for analysis
- Support agent evolution through performance feedback

**Key Components:**
- **Job Queue System**: Manages evaluation tasks with persistence
- **Worker Processes**: Execute tasks, validation, and evolution
- **Metrics Collection**: Aggregates results into actionable insights
- **Orchestrator**: Coordinates all system components

## Directory Structure

```
src/agent-eval/
├── orchestrator/                    # Core orchestration system
│   ├── config.json                 # System configuration
│   ├── job_queue.json             # Persistent job storage
│   ├── orchestrator.py            # Main orchestrator
│   ├── job_queue.py               # Job queue implementation
│   ├── evaluate_epoch.py          # Epoch evaluation script
│   └── workers/                   # Worker processes
│       ├── task-worker.py         # Task execution worker
│       ├── validation-worker.py   # Code validation worker
│       └── evolution-worker.py    # Evolution worker (future)
├── epochs/                        # Agent versions storage
│   └── epoch-001/                 # Example epoch
│       ├── agent-src/             # Agent source code
│       ├── runs/                  # Task execution results
│       ├── metrics/               # Performance reports
│       ├── compilation-check/     # Compilation artifacts
│       └── evolution-workspace/   # Evolution work area
├── default-workspaces/            # Template tasks
│   ├── task-001/                  # "Hello World" task
│   ├── task-002/                  # Calculator task
│   ├── task-003/                  # List operations
│   ├── task-004/                  # File I/O
│   └── task-005/                  # String processing
└── evaluation/                    # Metrics and analysis
    └── metrics-collectors/        # Metrics tools
```

## Prerequisites

### System Requirements
- Python 3.8+ installed
- Docker and Docker Compose installed
- Git repository access
- Sufficient disk space (1GB+ recommended)

### Environment Setup
```bash
# Navigate to system directory
cd src/agent-eval

# Verify Python installation
python3 --version

# Verify Docker installation
docker --version
docker-compose --version

# Check directory structure
ls -la
```

### Configuration Verification
```bash
# Check orchestrator configuration
cd orchestrator
python3 -c "from config_simple import load_config; print('Config OK')"

# Verify job queue system
python3 -c "from job_queue import JobQueue; print('Job Queue OK')"
```

## Quick Start Guide

### 1. Initial System Check
```bash
cd src/agent-eval/orchestrator

# Test basic functionality
python3 test_job_queue.py
python3 test_orchestrator.py
python3 test_evaluate_epoch.py

# Expected output: "All tests passed!"
```

### 2. Start the Orchestrator
```bash
# Start the job processing system
python3 orchestrator.py --start

# Check system status
python3 orchestrator.py --status

# Stop the system when done
python3 orchestrator.py --stop
```

### 3. Run Your First Evaluation
```bash
# Evaluate epoch-001 against all default tasks
python3 evaluate_epoch.py --epoch epoch-001 --parallel

# Expected output: Evaluation summary with task results
```

## Setting Up New Runs

### Creating a New Epoch

1. **Copy Existing Epoch Structure:**
```bash
cd src/agent-eval/epochs

# Create new epoch directory
mkdir epoch-002
cd epoch-002

# Copy structure from epoch-001
cp -r ../epoch-001/agent-src ./
mkdir -p runs metrics compilation-check evolution-workspace
```

2. **Modify Agent Code:**
```bash
cd epoch-002/agent-src

# Edit agent.py with your improvements
nano agent.py

# Update requirements.txt if needed
nano requirements.txt

# Test Docker build
docker-compose build
```

3. **Verify Epoch Setup:**
```bash
# Test agent execution (dry run)
cd src/agent-eval/orchestrator
python3 evaluate_epoch.py --epoch epoch-002 --parallel

# Check for any setup issues
ls -la ../epochs/epoch-002/runs/
```

### Adding New Tasks

1. **Create Task Directory:**
```bash
cd src/agent-eval/default-workspaces

# Create new task directory
mkdir task-006
cd task-006

# Create required subdirectories
mkdir input expected-output tests
```

2. **Define Task Requirements:**
```bash
# Create task description
cat > input/TASK.md << 'EOF'
# Task 006: [Task Name]

## Objective
[Describe what the agent should implement]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Input Format
[Describe expected inputs]

## Output Format
[Describe expected outputs]

## Example
```python
# Expected usage
result = your_function(input_data)
```
EOF
```

3. **Create Expected Output:**
```bash
# Create reference implementation
cat > expected-output/your_solution.py << 'EOF'
# Reference implementation
def your_function(input_data):
    # Implementation here
    return result
EOF
```

4. **Create Tests:**
```bash
# Create test file
cat > tests/test_your_solution.py << 'EOF'
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'output'))

import pytest
from your_solution import your_function

def test_basic_functionality():
    # Test basic case
    assert your_function("test") == expected_result

def test_edge_cases():
    # Test edge cases
    pass
EOF
```

## Running Evaluations

### Manual Evaluation Process

1. **Prepare Environment:**
```bash
cd src/agent-eval/orchestrator

# Ensure orchestrator is running
python3 orchestrator.py --status

# If not running, start it
python3 orchestrator.py --start
```

2. **Run Epoch Evaluation:**
```bash
# Full epoch evaluation (all tasks)
python3 evaluate_epoch.py --epoch epoch-001 --parallel

# Sequential evaluation (slower but more stable)
python3 evaluate_epoch.py --epoch epoch-001 --sequential

# Custom timeout (default 30 minutes)
python3 evaluate_epoch.py --epoch epoch-001 --parallel --timeout 45
```

3. **Monitor Progress:**
```bash
# Check job queue status
python3 orchestrator.py --status

# View detailed queue information
python3 -c "
from job_queue import JobQueue
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
print(jq.get_queue_stats())
"
```

### Single Task Evaluation

For testing specific tasks:

```bash
# Add single task to queue
python3 -c "
from job_queue import JobQueue, JobType
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
job_id = jq.enqueue(JobType.EVALUATE_TASK, {
    'epoch': 'epoch-001',
    'task': 'task-001'
})
print(f'Enqueued job: {job_id}')
"

# Monitor specific job
python3 -c "
from job_queue import JobQueue
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
job = jq.get_job('YOUR_JOB_ID')
print(f'Status: {job.status if job else \"Not found\"}')
"
```

## Data Flow and Storage

### Execution Data Flow

1. **Task Setup:**
   - Default workspaces copied to `epochs/{epoch}/runs/{task}/`
   - Output directory created for agent results

2. **Task Execution:**
   - Docker container runs agent with mounted task workspace
   - Agent generates code in `output/` directory
   - Logs captured in `output/` directory

3. **Validation:**
   - Generated code compiled and tested
   - Results stored in job queue with artifacts
   - Scores calculated (compilation + tests = 0-2 points)

4. **Metrics Collection:**
   - Job results aggregated into epoch scores
   - Reports generated in `epochs/{epoch}/metrics/`
   - Comparison reports in `evaluation/reports/`

### Storage Locations

**Job Queue Data:**
```bash
orchestrator/job_queue.json           # All job states and results
```

**Task Execution Results:**
```bash
epochs/{epoch}/runs/{task}/
├── input/                            # Task description (copied)
├── expected-output/                  # Reference implementation (copied)
├── tests/                           # Test files (copied)
└── output/                          # Agent-generated files
    ├── {solution}.py                # Agent's code
    └── execution.log                # Execution logs
```

**Performance Reports:**
```bash
epochs/{epoch}/metrics/
├── {epoch}_report_{timestamp}.json  # Detailed performance report
├── {epoch}_tasks_{timestamp}.csv    # Task-level CSV data
└── evaluation_summary.json         # Latest evaluation summary

evaluation/reports/
├── epoch_comparison_{timestamp}.json # Cross-epoch comparisons
└── epoch_comparison_{timestamp}.csv  # Comparison CSV data
```

**Configuration and State:**
```bash
orchestrator/config.json             # System configuration
orchestrator/job_queue.json          # Persistent job queue
```

## Monitoring and Troubleshooting

### System Health Checks

1. **Check Orchestrator Status:**
```bash
cd src/agent-eval/orchestrator

# Quick status check
python3 orchestrator.py --status

# Detailed job queue inspection
python3 -c "
from job_queue import JobQueue
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
stats = jq.get_queue_stats()
print(f'Pending: {stats[\"pending\"]}')
print(f'Running: {stats[\"running\"]}')
print(f'Completed: {stats[\"completed\"]}')
print(f'Failed: {stats[\"failed\"]}')
"
```

2. **Monitor Worker Processes:**
```bash
# Check if workers are running
ps aux | grep -E "(task-worker|validation-worker)"

# Check Docker containers
docker ps
```

3. **Check Disk Space:**
```bash
# Check available space
df -h

# Check evaluation directory size
du -sh src/agent-eval/
```

### Common Issues and Solutions

**Issue: Jobs stuck in RUNNING state**
```bash
# Check for hung processes
ps aux | grep python3

# Restart orchestrator
python3 orchestrator.py --stop
python3 orchestrator.py --start

# Reset stuck jobs
python3 orchestrator.py --retry-failed
```

**Issue: Docker build failures**
```bash
# Check Docker logs
cd epochs/{epoch}/agent-src
docker-compose logs

# Rebuild with no cache
docker-compose build --no-cache

# Check for port conflicts
docker ps
```

**Issue: API rate limiting**
```bash
# Check recent job failures
python3 -c "
from job_queue import JobQueue
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
for job_id, job in jq.jobs.items():
    if job.status.value == 'failed' and job.result:
        print(f'{job_id}: {job.result.error}')
"

# Adjust rate limiting in config
nano config.json
# Reduce api_requests_per_minute
```

### Log Locations

**System Logs:**
```bash
# Orchestrator output (when run in foreground)
python3 orchestrator.py --start  # See stdout

# Worker process output
# Check terminal where orchestrator was started

# Docker container logs
docker-compose logs -f  # In agent-src directory
```

**Task Execution Logs:**
```bash
# Individual task logs
cat epochs/{epoch}/runs/{task}/output/execution.log

# Agent output files
ls -la epochs/{epoch}/runs/{task}/output/
```

## Metrics and Reports

### Generating Performance Reports

1. **Basic Epoch Report:**
```bash
cd src/agent-eval/evaluation/metrics-collectors

# Score summary
python3 metrics_cli.py score --epoch epoch-001

# Detailed reports
python3 metrics_cli.py report --epoch epoch-001

# Validation debugging
python3 metrics_cli.py score --epoch epoch-001 --validation-summary
```

2. **Cross-Epoch Analysis:**
```bash
# Compare multiple epochs
python3 metrics_cli.py report --compare epoch-001 epoch-002

# Trend analysis
python3 metrics_cli.py analyze --epochs epoch-001 epoch-002 epoch-003

# Focus on specific analysis
python3 metrics_cli.py analyze --epochs epoch-001 epoch-002 --trends-only
```

3. **Custom Reports:**
```bash
# Save to specific location
python3 metrics_cli.py report --epoch epoch-001 --output-dir /path/to/reports

# JSON only format
python3 metrics_cli.py report --epoch epoch-001 --formats json

# Analysis with output file
python3 metrics_cli.py analyze --epochs epoch-001 epoch-002 --output analysis.json
```

### Understanding Metrics

**Score Interpretation:**
- **2/2**: Perfect score (compiles + passes tests)
- **1/2**: Partial success (compiles but tests fail, or syntax errors)
- **0/2**: Complete failure (no valid code generated)

**Success Rates:**
- **Overall Success Rate**: Percentage of maximum possible points achieved
- **Compilation Success Rate**: Percentage of tasks that generated valid Python
- **Test Success Rate**: Percentage of tasks that passed functional tests

**Trend Indicators:**
- **📈 Improving**: >5% increase from first to last epoch
- **📉 Declining**: >5% decrease from first to last epoch  
- **➡️ Stable**: Within ±5% change

## Manual Operations

### Job Queue Management

1. **Clear Failed Jobs:**
```bash
cd src/agent-eval/orchestrator

# Retry all failed jobs
python3 orchestrator.py --retry-failed

# Or manually clear queue
python3 -c "
from job_queue import JobQueue
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
# Clear all jobs (DANGEROUS!)
# jq.jobs.clear()
# jq._save_jobs()
"
```

2. **Add Custom Jobs:**
```bash
# Add evaluation job
python3 -c "
from job_queue import JobQueue, JobType
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
job_id = jq.enqueue(JobType.EVALUATE_TASK, {
    'epoch': 'epoch-001',
    'task': 'task-003'
})
print(f'Added job: {job_id}')
"

# Add validation job
python3 -c "
from job_queue import JobQueue, JobType
from config_simple import load_config
jq = JobQueue(load_config().job_queue_file)
job_id = jq.enqueue(JobType.COMPILE_CHECK, {
    'epoch': 'epoch-001',
    'task': 'task-003'
})
print(f'Added validation job: {job_id}')
"
```

### Manual Task Execution

For debugging specific issues:

1. **Run Single Task Manually:**
```bash
cd epochs/epoch-001/agent-src

# Set environment
export TASK_ID=task-001

# Run container manually
docker-compose up --build

# Check results
ls -la ../runs/task-001/output/
```

2. **Manual Validation:**
```bash
cd epochs/epoch-001/runs/task-001

# Test compilation
python3 -m py_compile output/*.py

# Run tests manually
python3 -m pytest tests/ -v
```

### Configuration Management

1. **View Current Configuration:**
```bash
cd src/agent-eval/orchestrator

python3 -c "
from config_simple import load_config
import json
config = load_config()
print(json.dumps(config.__dict__, indent=2, default=str))
"
```

2. **Modify Configuration:**
```bash
# Edit configuration file
nano config.json

# Or create custom config
cat > custom_config.json << 'EOF'
{
  "parallelism": {
    "max_concurrent_jobs": 10,
    "task_evaluation_workers": 3,
    "validation_workers": 2,
    "evolution_workers": 1
  },
  "rate_limiting": {
    "api_requests_per_minute": 30,
    "retry_backoff_seconds": 60
  },
  "timeouts": {
    "task_execution_timeout": 300,
    "validation_timeout": 120,
    "evolution_timeout": 600,
    "job_queue_poll_interval": 2
  }
}
EOF

# Use custom config
python3 orchestrator.py --start --config custom_config.json
```

## Cleanup and Maintenance

### Regular Cleanup Tasks

1. **Clean Old Job Data:**
```bash
cd src/agent-eval/orchestrator

# Backup current job queue
cp job_queue.json job_queue_backup_$(date +%Y%m%d).json

# Clean completed jobs older than 7 days
python3 -c "
from job_queue import JobQueue, JobStatus
from config_simple import load_config
from datetime import datetime, timedelta
import json

jq = JobQueue(load_config().job_queue_file)
cutoff = datetime.now() - timedelta(days=7)
cleaned = 0

for job_id in list(jq.jobs.keys()):
    job = jq.jobs[job_id]
    if (job.status == JobStatus.COMPLETED and 
        job.completed_at and job.completed_at < cutoff):
        del jq.jobs[job_id]
        cleaned += 1

jq._save_jobs()
print(f'Cleaned {cleaned} old completed jobs')
"
```

2. **Archive Old Epochs:**
```bash
cd src/agent-eval

# Create archive directory
mkdir -p archives

# Archive old epoch (keep runs data)
tar -czf archives/epoch-001_$(date +%Y%m%d).tar.gz epochs/epoch-001/

# Verify archive
tar -tzf archives/epoch-001_$(date +%Y%m%d).tar.gz | head -10
```

3. **Clean Docker Resources:**
```bash
# Remove old containers
docker container prune -f

# Remove old images
docker image prune -f

# Clean build cache
docker builder prune -f
```

### System Reset

For a complete system reset (DESTRUCTIVE):

```bash
cd src/agent-eval

# Stop all processes
orchestrator/orchestrator.py --stop

# Backup important data
mkdir -p backups/$(date +%Y%m%d)
cp orchestrator/job_queue.json backups/$(date +%Y%m%d)/
cp -r epochs/ backups/$(date +%Y%m%d)/

# Reset job queue
echo '{}' > orchestrator/job_queue.json

# Clean all run data
find epochs/ -name "runs" -type d -exec rm -rf {} + 2>/dev/null || true
find epochs/ -name "metrics" -type d -exec rm -rf {} + 2>/dev/null || true

# Recreate directory structure
for epoch in epochs/*/; do
    mkdir -p "$epoch"/{runs,metrics,compilation-check,evolution-workspace}
done

echo "System reset complete. Restore from backups/ if needed."
```

### Troubleshooting Checklist

When things go wrong, check these items in order:

1. **✅ System Status:**
   - Orchestrator running? `python3 orchestrator.py --status`
   - Docker running? `docker ps`
   - Disk space available? `df -h`

2. **✅ Job Queue Health:**
   - Jobs processing? Check queue stats
   - Stuck jobs? `--retry-failed`
   - Rate limiting errors? Check API limits

3. **✅ Task Configuration:**
   - Task files present? Check `default-workspaces/`
   - Agent code valid? Test Docker build
   - Paths correct? Verify mount points

4. **✅ Output Validation:**
   - Files generated? Check `output/` directories
   - Tests running? Manual pytest execution
   - Compilation working? Manual py_compile

5. **✅ Metrics Collection:**
   - Validation jobs completing? Check job artifacts
   - Reports generating? Test metrics CLI
   - Data consistent? Compare manual vs automated results

---

## Quick Reference Commands

**Essential Commands:**
```bash
# Start system
cd src/agent-eval/orchestrator && python3 orchestrator.py --start

# Run evaluation
python3 evaluate_epoch.py --epoch epoch-001 --parallel

# Check status
python3 orchestrator.py --status

# Generate reports
cd ../evaluation/metrics-collectors
python3 metrics_cli.py score --epoch epoch-001
python3 metrics_cli.py report --epoch epoch-001

# Stop system
cd ../orchestrator && python3 orchestrator.py --stop
```

**Emergency Commands:**
```bash
# Force stop everything
pkill -f "python3.*orchestrator"
docker-compose down  # In each agent-src directory

# Reset stuck jobs
python3 orchestrator.py --retry-failed

# Clean system
docker system prune -f
```

This operations guide provides everything needed to run and maintain the agent evaluation system manually. Keep this document updated as the system evolves.