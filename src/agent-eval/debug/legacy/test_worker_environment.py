#!/usr/bin/env python3
"""
Test worker environment to debug why orchestrator workers don't work
"""

import os
import sys
import subprocess
from pathlib import Path

def test_worker_with_orchestrator_env():
    """Test running a worker with the exact same environment as orchestrator workers"""
    
    print("Testing worker environment...")
    
    # Get current working directory (same as orchestrator)
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Set up environment like orchestrator does
    env = os.environ.copy()
    env['WORKER_ID'] = 'test-env-worker'
    env['WORKER_TYPE'] = 'task_evaluation'
    
    # Get the script path (same as orchestrator)
    script_path = Path(cwd) / "workers" / "task-worker.py"
    print(f"Script path: {script_path}")
    print(f"Script exists: {script_path.exists()}")
    
    # Test 1: Run with subprocess.DEVNULL (like current orchestrator)
    print(f"\nTest 1: Running with DEVNULL (current orchestrator method)")
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )
        
        print(f"Started process PID: {process.pid}")
        
        # Wait a bit to see if it processes jobs
        import time
        time.sleep(10)
        
        # Check if process is still alive
        if process.poll() is None:
            print("Process still running, terminating...")
            process.terminate()
            process.wait()
        else:
            print(f"Process exited with code: {process.returncode}")
            
    except Exception as e:
        print(f"Error running with DEVNULL: {e}")
    
    # Test 2: Run with visible output
    print(f"\nTest 2: Running with visible output")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=env,
            timeout=10,
            capture_output=True,
            text=True
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
    except subprocess.TimeoutExpired as e:
        print("Process timed out (expected - worker runs in loop)")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
    except Exception as e:
        print(f"Error running with visible output: {e}")

if __name__ == "__main__":
    test_worker_with_orchestrator_env()