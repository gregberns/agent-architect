#!/usr/bin/env python3
"""
Debug version of task worker with verbose logging
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import orchestrator modules  
sys.path.insert(0, str(Path(__file__).parent.parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

def main():
    """Debug version of task worker"""
    worker_id = os.environ.get('WORKER_ID', 'debug-task-worker-verbose')
    
    print(f"DEBUG: Task worker {worker_id} starting")
    print(f"DEBUG: Current directory: {os.getcwd()}")
    print(f"DEBUG: Python path: {sys.path[:3]}")
    
    try:
        config = load_config()
        print(f"DEBUG: Config loaded, queue file: {config.job_queue_file}")
        
        job_queue = JobQueue(config.job_queue_file)
        print(f"DEBUG: Job queue initialized")
        
        # Get current stats
        stats = job_queue.get_queue_stats()
        print(f"DEBUG: Current queue stats: {stats}")
        
        running = True
        poll_count = 0
        
        while running and poll_count < 10:  # Limit to 10 polls for testing
            poll_count += 1
            print(f"\nDEBUG: Poll {poll_count} - checking for jobs...")
            
            try:
                # Get next job from queue
                job = job_queue.dequeue(worker_id)
                print(f"DEBUG: Dequeue result: {job}")
                
                if job is None:
                    print("DEBUG: No jobs available, sleeping...")
                    time.sleep(2)  # Shorter sleep for debugging
                    continue
                
                if job.job_type != JobType.EVALUATE_TASK:
                    print(f"DEBUG: Wrong job type: {job.job_type}")
                    job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}")
                    continue
                
                print(f"DEBUG: Processing job {job.id[:8]} - {job.parameters}")
                
                # Instead of actually executing, just complete it successfully
                result = JobResult(
                    success=True,
                    output="Debug task completed (no actual execution)",
                    execution_time=1.0,
                    artifacts={"debug": True}
                )
                
                job_queue.complete_job(job.id, result)
                print(f"DEBUG: Completed job {job.id[:8]}")
                
                # Exit after processing one job
                running = False
                
            except Exception as e:
                print(f"DEBUG: Error in polling loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
        
        print(f"DEBUG: Worker finished after {poll_count} polls")
        
    except Exception as e:
        print(f"DEBUG: Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()