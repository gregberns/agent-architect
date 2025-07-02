# Agent Evolution Script - Detailed Implementation Plan

## Overview
Create `evolve_epoch.py` script that takes a validated agent from a parent epoch, copies it to new epoch(s), provides it with validation logs from its performance, and runs an evolution process where the agent can improve itself.

## Script Arguments
```bash
python -m orchestrator.evolve_epoch --parent-epoch epoch-000 [--num-copies 1] [--config config.json]
```

- `--parent-epoch`: Source epoch (must have completed validation)
- `--num-copies`: Number of evolution epochs to create (default: 1)
- `--config`: Optional config file (similar to evaluate_epoch)

## Directory Structure Created

### For each new epoch (e.g., epoch-001):
```
epoch-001/
├── parent.json                    # Tracks parent epoch info
└── evolution/
    ├── agent-src/                 # Agent code to be evolved (copied from parent)
    │   ├── Dockerfile
    │   ├── agent.py
    │   ├── requirements.txt
    │   └── docker-compose.yml
    ├── input/                     # Everything the agent needs to analyze
    │   ├── agent-src/             # Reference copy of original agent code
    │   │   ├── Dockerfile
    │   │   ├── agent.py
    │   │   ├── requirements.txt
    │   │   ├── docker-compose.yml
    │   │   └── TASK.md            # REQUIRED: Evolution task instructions
    │   └── validation-logs/       # Parent epoch's validation results
    │       ├── metrics.csv        # Latest metrics CSV from parent
    │       └── task-results/      # Detailed results per task
    │           ├── mbpp-task-001/
    │           │   ├── test_logs.txt
    │           │   ├── container_logs.txt
    │           │   └── output/
    │           │       └── min_cost.py
    │           ├── mbpp-task-002/
    │           │   ├── test_logs.txt
    │           │   ├── container_logs.txt  
    │           │   └── output/
    │           │       └── similar_elements.py
    │           └── ... (all tasks)
    └── output/                    # Where evolved agent saves its improvements
```

## Implementation Phases

### Phase 1: Setup and Validation
1. **Validate Parent Epoch**
   - Check that parent epoch exists
   - Verify it has completed validation (has validation/evaluation_summary.json)
   - Ensure validation/metrics/ directory exists with CSV files

2. **Create New Epoch Structure**
   - **Find next available epoch numbers** (scan existing epochs directory)
   - Generate new epoch name(s) based on highest existing epoch + 1
   - Create directory structure as shown above
   - Handle multiple copies if num-copies > 1
   - **Never overwrite existing epochs**

3. **Copy Agent Source Code**
   - Copy parent's `validation/agent-src/` to new epoch's `evolution/agent-src/`
   - Copy same files to new epoch's `evolution/input/agent-src/` for reference

4. **Collect and Organize Validation Logs**
   - Find latest CSV file in parent's `validation/metrics/` directory
   - Copy to `evolution/input/validation-logs/metrics.csv`
   - For each task in parent's `validation/runs/`, copy:
     - `test_logs.txt`
     - `container_logs.txt` 
     - All files from `output/` directory
   - Organize in `evolution/input/validation-logs/task-results/[task-name]/`

5. **Create Parent Tracking File**
   - Create `parent.json` in epoch root with:
     ```json
     {
       "parent_epoch": "epoch-000",
       "created_at": "2025-07-02T10:30:00Z",
       "evolution_generation": 1,
       "parent_score": 15.0,
       "parent_success_rate": "100%"
     }
     ```

### Phase 2: Evolution Process
1. **Pre-Evolution Validation**
   - **CRITICAL**: Check that `evolution/input/agent-src/TASK.md` exists
   - If missing, show clear error and stop process:
     ```
     ❌ ERROR: Missing required TASK.md file
     
     The evolution process requires a TASK.md file that describes what the agent should do.
     Expected location: ./epochs/[epoch-name]/evolution/input/agent-src/TASK.md
     
     Please create this file with instructions for the agent's evolution task before continuing.
     ```

2. **Build Docker Image**
   - Build from `evolution/agent-src/Dockerfile`
   - Tag as `agent-evolution-[epoch-name]`
   - Handle build errors gracefully

3. **Run Evolution Container**
   - Mount `evolution/input/` as read-only to `/app/workspace/input`
   - Mount `evolution/output/` as read-write to `/app/workspace/output`
   - Set environment variables for evolution context
   - **Real-time log streaming**: Stream container logs to file while running
   - **Configurable timeout**: Default 10 minutes (600 seconds), configurable via config
   - **Preserve logs on failure**: Logs saved even if container hangs/crashes

3. **Handle Evolution Results**
   - Check if agent produced output files
   - Validate output structure
   - Log evolution process results
   - Save container logs for debugging

## Key Implementation Details

### Docker Container Execution
```python
# Real-time log streaming approach (not subprocess.run)
import subprocess
import threading
import time

# Start container in background
proc = subprocess.Popen([
    "docker", "run", "--rm", "-t", "--name", container_name,
    "--env-file", ".env",
    "-v", f"{evolution_dir}/input:/app/workspace/input:ro",  # Read-only
    "-v", f"{evolution_dir}/output:/app/workspace/output",   # Read-write
    "-v", f"{evolution_dir}/output:/app/logs",               # For debug logs
    image_tag
], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Stream logs to file in real-time (truncate/overwrite existing file)
log_file = evolution_dir / "evolution_container_logs.txt"
with open(log_file, 'w') as f:  # 'w' mode truncates existing file
    def stream_logs():
        for line in proc.stdout:
            f.write(line)
            f.flush()  # Ensure immediate write
            print(line.strip())  # Also show on console
    
    log_thread = threading.Thread(target=stream_logs)
    log_thread.start()
    
    # Wait with timeout (configurable, default 600 seconds)
    try:
        proc.wait(timeout=evolution_timeout)
    except subprocess.TimeoutExpired:
        print(f"⏰ Evolution timeout after {evolution_timeout} seconds")
        proc.kill()
    finally:
        log_thread.join()  # Ensure all logs are written
```

### Configuration Options
```json
{
  "evolution_timeout_seconds": 600,
  "evolution_container_memory": "2g",
  "evolution_log_level": "INFO"
}
```

### Error Handling
- Graceful handling of missing parent epoch
- Docker build/run failures
- Timeout scenarios
- Partial evolution results

### Logging and Output
- Console progress indicators with real-time container output
- **Real-time container logs**: `evolution/evolution_container_logs.txt`
- **Process logs**: `evolution/evolution_process_logs.txt` (setup, build, etc.)
- Summary of evolution process
- Clear success/failure indicators
- **Logs preserved on timeout/crash**: Never lost due to container issues

## Agent Evolution Expectations

The agent running in the evolution container will have access to:
1. **Its own source code** (`/app/workspace/input/agent-src/`)
2. **Validation performance data** (`/app/workspace/input/validation-logs/`)
   - Overall metrics showing which tasks failed
   - Detailed test logs showing specific failures
   - Container logs showing runtime issues
   - Output files showing what the agent actually produced vs expected

The agent should analyze this data and output improved versions of its files to `/app/workspace/output/`. This could include:
- Modified `agent.py` with bug fixes
- Updated `requirements.txt` with new dependencies
- Improved `Dockerfile` for better environment setup
- Documentation of changes made

## File Naming and Organization

### New Epoch Naming
- **Scan existing epochs**: Find highest existing epoch number
- **Increment from highest**: `epoch-000`, `epoch-002` exist → next is `epoch-003`
- **Sequential allocation**: Multiple copies get consecutive numbers
- **Never overwrite**: Always check if epoch exists before creating
- **Handle gaps gracefully**: If `epoch-001` is deleted, still increment from highest

**Examples:**
- Existing: `epoch-000`, `epoch-001` → Create: `epoch-002`
- Existing: `epoch-000`, `epoch-002`, `epoch-003` → Create: `epoch-004`
- Parent `epoch-002`, 2 copies → Create: `epoch-004`, `epoch-005`

### Log File Organization
- Keep original filenames for easy reference
- Organize by task for clear structure
- Include timestamps in evolution logs

## Integration with Existing System

### Relationship to evaluate_epoch.py
- Similar command-line interface and structure
- Reuse Docker utilities and error handling patterns
- Compatible with existing metrics collection system
- New evolved agents can be validated using existing evaluate_epoch.py

### Future Integration Points
- evolved epochs can become parent epochs for further evolution
- Metrics system can track evolution lineage
- Comparison reports between parent and evolved agents

## Command Examples

```bash
# Basic evolution - create next epoch from epoch-000
python -m orchestrator.evolve_epoch --parent-epoch epoch-000
# If epochs 000-002 exist, creates: epoch-003

# Create multiple evolution branches from epoch-000
python -m orchestrator.evolve_epoch --parent-epoch epoch-000 --num-copies 3
# If epochs 000-002 exist, creates: epoch-003, epoch-004, epoch-005

# Evolution from any epoch - always finds next available numbers
python -m orchestrator.evolve_epoch --parent-epoch epoch-002 --num-copies 2
# If epochs 000-005 exist, creates: epoch-006, epoch-007
```

## Success Criteria
1. ✅ New epoch directory structure created correctly
2. ✅ Agent source code copied to both locations
3. ✅ All validation logs properly organized and accessible
4. ✅ Parent tracking file created with accurate metadata
5. ✅ **TASK.md file validation before Docker execution**
6. ✅ Docker container runs successfully with proper mounts
7. ✅ Evolution process logs captured and saved
8. ✅ Output directory contains agent's evolution results
9. ✅ Process handles errors gracefully without corrupting data

## Next Steps After Implementation
1. Test with epoch-000 to create epoch-001
2. Verify evolved agent can be validated with evaluate_epoch.py
3. Test multi-copy functionality
4. Integration with metrics collection system
5. Documentation and usage examples