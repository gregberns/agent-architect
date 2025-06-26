#!/usr/bin/env python3
"""
Test job queue persistence and recovery
"""

import os
import tempfile
from job_queue import JobQueue, JobType, JobResult

def test_persistence_and_recovery():
    """Test that job queue persists and recovers correctly"""
    print("Testing Job Queue Persistence and Recovery...")
    
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # Create first queue instance and add jobs
        print("1. Creating initial queue and adding jobs...")
        queue1 = JobQueue(temp_file)
        
        job_id1 = queue1.enqueue(JobType.EVALUATE_TASK, {"epoch": "epoch-001", "task": "task-001"})
        job_id2 = queue1.enqueue(JobType.COMPILE_CHECK, {"task_id": job_id1})
        
        # Complete one job
        job = queue1.dequeue("worker-1")
        result = JobResult(success=True, output="Task completed", execution_time=2.5)
        queue1.complete_job(job.id, result)
        
        stats1 = queue1.get_queue_stats()
        print(f"   Initial stats: {stats1}")
        
        # Create second queue instance (simulating restart)
        print("2. Creating new queue instance (simulating restart)...")
        queue2 = JobQueue(temp_file)
        
        stats2 = queue2.get_queue_stats()
        print(f"   Recovered stats: {stats2}")
        
        # Verify data is the same
        if stats1 == stats2:
            print("✅ Persistence test passed - stats match!")
        else:
            print("❌ Persistence test failed - stats don't match!")
            return False
        
        # Test job details are preserved
        print("3. Testing job details preservation...")
        all_jobs1 = {job.id: job for job in queue1.get_all_jobs()}
        all_jobs2 = {job.id: job for job in queue2.get_all_jobs()}
        
        if len(all_jobs1) == len(all_jobs2):
            print(f"   Job count matches: {len(all_jobs1)}")
            
            # Check specific job details
            for job_id in all_jobs1:
                if job_id in all_jobs2:
                    job1 = all_jobs1[job_id]
                    job2 = all_jobs2[job_id]
                    if (job1.status == job2.status and 
                        job1.job_type == job2.job_type and
                        job1.parameters == job2.parameters):
                        print(f"   Job {job_id[:8]}... details match")
                    else:
                        print(f"   Job {job_id[:8]}... details don't match!")
                        return False
                else:
                    print(f"   Job {job_id[:8]}... missing in recovered queue!")
                    return False
        else:
            print("❌ Job count doesn't match!")
            return False
        
        print("✅ Job queue persistence and recovery test passed!")
        return True
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_configuration_defaults():
    """Test configuration loading and defaults"""
    print("\nTesting Configuration Defaults...")
    
    from config_simple import load_config, OrchestratorConfig
    
    # Test default configuration
    default_config = OrchestratorConfig.default()
    print(f"   Default max_concurrent_jobs: {default_config.parallelism.max_concurrent_jobs}")
    print(f"   Default max_retries: {default_config.rate_limiting.max_retries}")
    print(f"   Default task_timeout: {default_config.timeouts.task_execution_timeout}")
    
    # Test configuration to/from dict
    config_dict = default_config.to_dict()
    print(f"   Configuration dictionary has {len(config_dict)} top-level keys")
    
    # Test with non-existent config file (should create default)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_config_file = f.name
    
    try:
        os.remove(temp_config_file)  # Remove the file so it doesn't exist
        config = load_config(temp_config_file)
        
        if os.path.exists(temp_config_file):
            print("✅ Default configuration file created successfully")
        else:
            print("❌ Default configuration file not created")
            return False
            
        # Verify loaded config has expected defaults
        if (config.parallelism.max_concurrent_jobs == 5 and
            config.rate_limiting.max_retries == 5 and
            config.timeouts.task_execution_timeout == 300):
            print("✅ Configuration defaults loaded correctly")
            return True
        else:
            print("❌ Configuration defaults incorrect")
            return False
            
    finally:
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)

if __name__ == "__main__":
    success1 = test_persistence_and_recovery()
    success2 = test_configuration_defaults()
    
    if success1 and success2:
        print("\n🎉 All persistence and configuration tests passed!")
    else:
        print("\n❌ Some tests failed!")