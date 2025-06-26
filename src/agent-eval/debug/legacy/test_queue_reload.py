#!/usr/bin/env python3
"""
Test script to verify queue reload functionality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue
from config_simple import load_config

def test_queue_reload():
    """Test queue reload functionality"""
    
    config = load_config()
    job_queue = JobQueue(config.job_queue_file)
    
    print("Testing queue reload functionality...")
    print(f"Queue file: {config.job_queue_file}")
    
    # Get initial stats
    initial_stats = job_queue.get_queue_stats()
    print(f"Initial stats: {initial_stats}")
    
    # Get all jobs before reload
    all_jobs_before = dict(job_queue.jobs)
    print(f"Jobs before reload: {len(all_jobs_before)}")
    
    # Show status of first few jobs
    for i, (job_id, job) in enumerate(list(all_jobs_before.items())[:3]):
        print(f"  Job {i+1}: {job_id[:8]} - {job.status.value}")
    
    print("\nReloading from file...")
    job_queue.reload_from_file()
    
    # Get stats after reload
    after_stats = job_queue.get_queue_stats()
    print(f"Stats after reload: {after_stats}")
    
    # Get all jobs after reload
    all_jobs_after = dict(job_queue.jobs)
    print(f"Jobs after reload: {len(all_jobs_after)}")
    
    # Show status of first few jobs
    for i, (job_id, job) in enumerate(list(all_jobs_after.items())[:3]):
        print(f"  Job {i+1}: {job_id[:8]} - {job.status.value}")
    
    # Check if data changed
    if initial_stats == after_stats:
        print("✅ Stats are identical (expected if no concurrent changes)")
    else:
        print("🔄 Stats changed during reload")
    
    # Test getting specific completed jobs
    completed_jobs = [job for job in all_jobs_after.values() if job.status.value == 'completed']
    print(f"\nFound {len(completed_jobs)} completed jobs:")
    
    for job in completed_jobs[:3]:
        print(f"  {job.id[:8]} - {job.parameters.get('task', 'unknown')} - {job.status.value}")
        
        # Test get_job method
        retrieved_job = job_queue.get_job(job.id)
        if retrieved_job:
            print(f"    ✅ get_job() works: {retrieved_job.status.value}")
        else:
            print(f"    ❌ get_job() failed!")

if __name__ == "__main__":
    test_queue_reload()