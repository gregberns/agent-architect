#!/usr/bin/env python3
"""
Debug worker to test the actual worker polling logic
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import orchestrator modules  
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

def main():
    """Debug worker that mimics the task worker logic"""
    worker_id = "debug-task-worker"
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    print(f"Debug worker {worker_id} starting...")
    print(f"Config file: {config.job_queue_file}")
    print(f"Poll interval: {config.timeouts.job_queue_poll_interval}")
    
    # Try polling a few times
    for i in range(5):
        print(f"\nPoll attempt {i+1}...")
        
        try:
            # Get next job from queue
            job = job_queue.dequeue(worker_id)
            
            if job is None:
                print("  No jobs available")
                time.sleep(config.timeouts.job_queue_poll_interval)
                continue
            
            print(f"  Got job: {job.id[:8]}")
            print(f"  Job type: {job.job_type}")
            print(f"  Parameters: {job.parameters}")
            
            if job.job_type != JobType.EVALUATE_TASK:
                print(f"  Wrong job type for task worker: {job.job_type}")
                job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}")
                continue
            
            # Simulate quick processing
            print("  Processing job...")
            time.sleep(1)
            
            # Complete the job successfully
            result = JobResult(
                success=True,
                output="Debug test completed successfully",
                execution_time=1.0
            )
            job_queue.complete_job(job.id, result)
            print(f"  Completed job {job.id[:8]} successfully")
            
            # Exit after processing one job
            break
            
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)
    
    print("Debug worker finished")

if __name__ == "__main__":
    main()