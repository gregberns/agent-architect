#!/usr/bin/env python3
"""
Simple test script for job queue functionality
"""

import os
import tempfile
from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

def test_job_queue():
    """Test basic job queue operations"""
    print("Testing Job Queue...")
    
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # Create job queue
        queue = JobQueue(temp_file)
        
        # Test enqueueing jobs
        print("1. Testing job enqueueing...")
        job_id1 = queue.enqueue(JobType.EVALUATE_TASK, {"epoch": "epoch-001", "task": "task-001"})
        job_id2 = queue.enqueue(JobType.COMPILE_CHECK, {"task_id": job_id1})
        print(f"   Created jobs: {job_id1[:8]}..., {job_id2[:8]}...")
        
        # Test getting queue stats
        print("2. Testing queue stats...")
        stats = queue.get_queue_stats()
        print(f"   Queue stats: {stats}")
        
        # Test dequeuing
        print("3. Testing job dequeuing...")
        job = queue.dequeue("worker-1")
        if job:
            print(f"   Dequeued job: {job.id[:8]}... ({job.job_type.value})")
            
            # Test completing job
            result = JobResult(success=True, output="Task completed successfully", execution_time=5.2)
            queue.complete_job(job.id, result)
            print(f"   Completed job: {job.id[:8]}...")
        
        # Test failing a job
        print("4. Testing job failure...")
        job2 = queue.dequeue("worker-2")
        if job2:
            queue.fail_job(job2.id, "Simulated failure", allow_retry=True)
            print(f"   Failed job: {job2.id[:8]}... (will retry)")
        
        # Final stats
        print("5. Final queue stats...")
        final_stats = queue.get_queue_stats()
        print(f"   Final stats: {final_stats}")
        
        print("✅ Job queue test completed successfully!")
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_config():
    """Test configuration loading"""
    print("\nTesting Configuration...")
    
    try:
        config = load_config()
        print(f"   Max concurrent jobs: {config.parallelism.max_concurrent_jobs}")
        print(f"   API requests per minute: {config.rate_limiting.api_requests_per_minute}")
        print(f"   Task timeout: {config.timeouts.task_execution_timeout}s")
        print("✅ Configuration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

if __name__ == "__main__":
    test_job_queue()
    test_config()