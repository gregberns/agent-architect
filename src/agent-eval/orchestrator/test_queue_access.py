#!/usr/bin/env python3
"""
Test script to debug job queue access
"""

import sys
from pathlib import Path

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue
from config_simple import load_config

def main():
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    print("Testing job queue access...")
    print(f"Queue file: {config.job_queue_file}")
    
    # Try to dequeue a job
    job = job_queue.dequeue("test-debug-worker")
    
    if job:
        print(f"Successfully dequeued job: {job.id[:8]}")
        print(f"Job type: {job.job_type}")
        print(f"Job parameters: {job.parameters}")
        
        # Put it back immediately
        job_queue.fail_job(job.id, "Debug test - putting job back to pending")
        job_queue.reset_running_jobs()
        print("Put job back to pending")
    else:
        print("No jobs available to dequeue")
    
    # Show current queue status
    stats = job_queue.get_queue_stats()
    print(f"\nQueue stats:")
    for status, count in stats.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()