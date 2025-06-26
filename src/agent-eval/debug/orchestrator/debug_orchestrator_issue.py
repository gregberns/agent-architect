#!/usr/bin/env python3
"""
Debug script to help diagnose the orchestrator job processing issue
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobStatus
from config_simple import load_config

def main():
    """Debug the orchestrator issue step by step"""
    
    print("🔍 ORCHESTRATOR DEBUG ANALYSIS")
    print("=" * 50)
    
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    # Step 1: Clear the queue and enqueue fresh jobs
    print("\n1. Clearing queue and enqueuing fresh jobs...")
    cleared = job_queue.clear_all_jobs()
    print(f"   Cleared {cleared} old jobs")
    
    # Enqueue 3 test jobs
    job_ids = []
    for i in range(1, 4):
        job_id = job_queue.enqueue(
            JobType.EVALUATE_TASK,
            {
                'epoch': 'epoch-001',
                'task': f'task-00{i}',
                'evaluation_run': True
            },
            max_retries=2
        )
        job_ids.append(job_id)
        print(f"   Enqueued task-00{i}: {job_id[:8]}")
    
    # Step 2: Check initial queue state
    print(f"\n2. Initial queue state:")
    stats = job_queue.get_queue_stats()
    print(f"   Queue stats: {stats}")
    
    # Step 3: Check if worker log files exist
    print(f"\n3. Checking for worker log files...")
    # Updated to use new runtime directory structure
    agent_eval_root = Path(__file__).parent.parent.parent
    log_dir = agent_eval_root / "runtime" / "logs" / "workers"
    log_files = list(log_dir.glob("worker-*.log")) if log_dir.exists() else []
    print(f"   Found {len(log_files)} worker log files:")
    for log_file in log_files:
        print(f"     - {log_file.name}")
    
    # Step 4: Monitor for activity
    print(f"\n4. Monitoring for 30 seconds...")
    print("   (In another terminal, start the orchestrator if not running)")
    print("   Watching for:")
    print("     - Job status changes")
    print("     - Worker log file updates")
    print("     - Job queue file modifications")
    
    queue_file = Path(config.job_queue_file)
    initial_mtime = queue_file.stat().st_mtime if queue_file.exists() else 0
    
    for i in range(30):
        time.sleep(1)
        
        # Check queue file modification
        current_mtime = queue_file.stat().st_mtime if queue_file.exists() else 0
        if current_mtime > initial_mtime:
            print(f"   ✅ Queue file updated at second {i+1}")
            initial_mtime = current_mtime
        
        # Check job statuses every 5 seconds
        if (i + 1) % 5 == 0:
            job_queue.reload_from_file()
            pending = running = completed = failed = 0
            
            for job_id in job_ids:
                job = job_queue.get_job(job_id)
                if job:
                    if job.status == JobStatus.PENDING:
                        pending += 1
                    elif job.status == JobStatus.RUNNING:
                        running += 1
                    elif job.status == JobStatus.COMPLETED:
                        completed += 1
                    elif job.status == JobStatus.FAILED:
                        failed += 1
            
            print(f"   📊 Second {i+1}: {pending}P {running}R {completed}C {failed}F")
            
            if completed == len(job_ids):
                print("   🎉 All jobs completed!")
                break
    
    # Step 5: Final analysis
    print(f"\n5. Final analysis:")
    
    # Check final job states
    job_queue.reload_from_file()
    print("   Final job states:")
    for job_id in job_ids:
        job = job_queue.get_job(job_id)
        if job:
            task = job.parameters.get('task', 'unknown')
            print(f"     {task}: {job.status.value}")
            if job.worker_id:
                print(f"       Processed by: {job.worker_id}")
        else:
            print(f"     {job_id[:8]}: NOT FOUND")
    
    # Check worker logs
    print("   Worker log activity:")
    for log_file in log_dir.glob("worker-*.log"):
        if log_file.exists():
            lines = len(log_file.read_text().strip().split('\n')) if log_file.stat().st_size > 0 else 0
            size = log_file.stat().st_size
            print(f"     {log_file.name}: {lines} lines, {size} bytes")
            
            # Show last few lines if there are any
            if size > 0:
                last_lines = log_file.read_text().strip().split('\n')[-3:]
                for line in last_lines:
                    print(f"       {line}")
    
    print(f"\n6. Next steps:")
    print("   - If jobs are still PENDING: orchestrator workers aren't polling")
    print("   - If worker logs are empty: workers aren't starting properly")  
    print("   - If worker logs show polling but no jobs: queue access issue")
    print("   - If jobs completed: system working correctly")

if __name__ == "__main__":
    main()