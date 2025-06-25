#!/usr/bin/env python3
"""
Test evaluate_epoch with debugging to see exactly what's happening
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobStatus
from config_simple import load_config

def simulate_evaluate_epoch():
    """Simulate what evaluate_epoch does with debugging"""
    
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    print("SIMULATE: Starting evaluation simulation...")
    
    # Clear old jobs first
    print("SIMULATE: Clearing old jobs...")
    cleared = job_queue.clear_all_jobs()
    print(f"SIMULATE: Cleared {cleared} old jobs")
    
    # Check initial state
    initial_stats = job_queue.get_queue_stats()
    print(f"SIMULATE: Initial stats: {initial_stats}")
    
    # Enqueue jobs like evaluate_epoch does
    print("SIMULATE: Enqueuing jobs...")
    job_ids = []
    tasks = ['task-001', 'task-002', 'task-003', 'task-004', 'task-005']
    
    for task in tasks:
        job_id = job_queue.enqueue(
            JobType.EVALUATE_TASK,
            {
                'epoch': 'epoch-001',
                'task': task,
                'evaluation_run': True
            },
            max_retries=2
        )
        job_ids.append(job_id)
        print(f"SIMULATE: Enqueued {task}: {job_id[:8]}")
    
    # Check stats after enqueuing
    after_enqueue_stats = job_queue.get_queue_stats()
    print(f"SIMULATE: Stats after enqueue: {after_enqueue_stats}")
    
    # Show the actual jobs we'll monitor
    print(f"SIMULATE: Will monitor these {len(job_ids)} job IDs:")
    for i, job_id in enumerate(job_ids):
        job = job_queue.get_job(job_id)
        if job:
            print(f"  {i+1}. {job_id[:8]} - {job.parameters.get('task', 'unknown')} - {job.status.value}")
        else:
            print(f"  {i+1}. {job_id[:8]} - NOT FOUND!")
    
    # Simulate monitoring loop (like evaluate_epoch does)
    print(f"\nSIMULATE: Starting monitoring loop...")
    
    for poll in range(5):  # Do 5 polls
        print(f"\nSIMULATE: Poll {poll + 1}")
        
        # Reload like evaluate_epoch does
        job_queue.reload_from_file()
        
        # Check status of monitored jobs
        completed_jobs = 0
        running_jobs = 0
        failed_jobs = 0
        pending_jobs = 0
        
        for job_id in job_ids:
            job = job_queue.get_job(job_id)
            if not job:
                print(f"SIMULATE: ERROR - Job {job_id[:8]} not found!")
                continue
            
            if job.status == JobStatus.COMPLETED:
                completed_jobs += 1
            elif job.status == JobStatus.RUNNING:
                running_jobs += 1
            elif job.status == JobStatus.FAILED:
                failed_jobs += 1
            elif job.status == JobStatus.PENDING:
                pending_jobs += 1
        
        print(f"SIMULATE: Status: {completed_jobs} done, {running_jobs} running, {failed_jobs} failed, {pending_jobs} pending")
        
        # Get overall queue stats
        overall_stats = job_queue.get_queue_stats()
        print(f"SIMULATE: Queue stats: {overall_stats}")
        
        if completed_jobs == len(job_ids):
            print("SIMULATE: All jobs completed!")
            break
        
        time.sleep(2)  # Wait 2 seconds between polls
    
    print("\nSIMULATE: Monitoring finished")

if __name__ == "__main__":
    simulate_evaluate_epoch()