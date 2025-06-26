#!/usr/bin/env python3
"""
Debug version of evaluate_epoch to see what job IDs it's monitoring
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobStatus
from config_simple import load_config

def debug_job_monitoring():
    """Debug what jobs are being monitored"""
    
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    print("DEBUG: Checking current queue state...")
    
    # Get all jobs in queue
    all_jobs = dict(job_queue.jobs)
    print(f"Total jobs in queue: {len(all_jobs)}")
    
    # Group by status
    by_status = {}
    for job in all_jobs.values():
        status = job.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(job)
    
    print("\nJobs by status:")
    for status, jobs in by_status.items():
        print(f"  {status}: {len(jobs)}")
        for job in jobs[:3]:  # Show first 3
            print(f"    {job.id[:8]} - {job.parameters.get('task', 'unknown')} - created {job.created_at}")
    
    # Show most recent jobs (likely from current run)
    all_jobs_list = list(all_jobs.values())
    all_jobs_list.sort(key=lambda x: x.created_at, reverse=True)
    
    print(f"\nMost recent 10 jobs:")
    for i, job in enumerate(all_jobs_list[:10]):
        print(f"  {i+1}. {job.id[:8]} - {job.parameters.get('task', 'unknown')} - {job.status.value} - {job.created_at}")
    
    # Simulate what evaluate_epoch monitoring would see
    print(f"\nSimulating evaluate_epoch monitoring...")
    
    # Get the 5 most recent job IDs (these are likely what evaluate_epoch is monitoring)
    recent_job_ids = [job.id for job in all_jobs_list[:5]]
    
    print(f"Would monitor these 5 jobs:")
    for job_id in recent_job_ids:
        job = job_queue.get_job(job_id)
        if job:
            print(f"  {job_id[:8]} - {job.parameters.get('task', 'unknown')} - {job.status.value}")
        else:
            print(f"  {job_id[:8]} - NOT FOUND!")
    
    # Check stats
    stats = job_queue.get_queue_stats()
    print(f"\nQueue stats: {stats}")

if __name__ == "__main__":
    debug_job_monitoring()