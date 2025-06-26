#!/usr/bin/env python3
"""
Test Docker execution directly to see what's failing
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_simple import load_config

def test_docker_execution():
    """Test the exact Docker execution logic from task worker"""
    
    # Use the remaining job parameters
    epoch = 'epoch-001'
    task = 'task-005'  # One of the remaining pending jobs
    
    print(f"Testing Docker execution for {epoch}/{task}")
    
    # Build paths (same as task worker)
    base_dir = Path(__file__).parent.parent
    epoch_dir = base_dir / "epochs" / epoch
    agent_src_dir = epoch_dir / "agent-src"
    
    print(f"Base dir: {base_dir}")
    print(f"Epoch dir: {epoch_dir}")
    print(f"Agent src dir: {agent_src_dir}")
    print(f"Agent src exists: {agent_src_dir.exists()}")
    
    if not agent_src_dir.exists():
        print(f"ERROR: Agent source directory not found: {agent_src_dir}")
        return
    
    # Check docker-compose.yml exists
    compose_file = agent_src_dir / "docker-compose.yml"
    print(f"Docker compose file: {compose_file}")
    print(f"Compose file exists: {compose_file.exists()}")
    
    if compose_file.exists():
        print("Docker compose file contents:")
        with open(compose_file) as f:
            print(f.read())
    
    # Load config for timeout
    config = load_config()
    
    # Try the Docker execution
    print(f"\nAttempting Docker execution with timeout {config.timeouts.task_execution_timeout}s...")
    
    start_time = time.time()
    
    env = os.environ.copy()
    env['TASK_ID'] = task
    
    print(f"Environment TASK_ID set to: {task}")
    print(f"Working directory: {agent_src_dir}")
    
    try:
        result = subprocess.run(
            ["docker-compose", "up", "--build"],
            cwd=agent_src_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30  # Shorter timeout for testing
        )
        
        execution_time = time.time() - start_time
        
        print(f"Execution completed in {execution_time:.2f}s")
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        # Check output files
        task_output_dir = epoch_dir / "runs" / task / "output"
        print(f"\nChecking output directory: {task_output_dir}")
        print(f"Output dir exists: {task_output_dir.exists()}")
        
        if task_output_dir.exists():
            output_files = list(task_output_dir.glob("*.py"))
            print(f"Generated {len(output_files)} Python files: {[f.name for f in output_files]}")
        
    except subprocess.TimeoutExpired as e:
        print(f"Docker execution timed out after 30s")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
    except Exception as e:
        print(f"Docker execution error: {e}")

if __name__ == "__main__":
    test_docker_execution()