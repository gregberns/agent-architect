#!/usr/bin/env python3
"""
Test orchestrator functionality
"""

import time
import tempfile
import threading
from pathlib import Path

from job_queue import JobQueue, JobType
from orchestrator import Orchestrator

def test_orchestrator_basic():
    """Test basic orchestrator functionality"""
    print("Testing Orchestrator Basic Functionality...")
    
    # Create temporary config for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_config = f.name
    
    try:
        # Create orchestrator instance
        orchestrator = Orchestrator()
        
        # Test status without starting
        status = orchestrator.get_status()
        print(f"   Initial status: {status['running']}")
        print(f"   Workers configured: task={orchestrator.config.parallelism.task_evaluation_workers}, "
              f"evolution={orchestrator.config.parallelism.evolution_workers}, "
              f"validation={orchestrator.config.parallelism.validation_workers}")
        
        # Test job queue access
        job_id = orchestrator.job_queue.enqueue(JobType.EVALUATE_TASK, {"epoch": "epoch-001", "task": "task-001"})
        print(f"   Enqueued test job: {job_id[:8]}...")
        
        # Test status with job in queue
        status = orchestrator.get_status()
        print(f"   Queue has {status['queue']['pending']} pending jobs")
        
        # Test retry functionality
        retried = orchestrator.retry_failed_jobs()
        print(f"   Retried {retried} failed jobs")
        
        print("✅ Orchestrator basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

def test_worker_script_existence():
    """Test that worker scripts exist"""
    print("\nTesting Worker Scripts...")
    
    workers_dir = Path(__file__).parent / "workers"
    required_workers = [
        "task-worker.py",
        "evolution-worker.py", 
        "validation-worker.py"
    ]
    
    all_exist = True
    for worker_script in required_workers:
        script_path = workers_dir / worker_script
        if script_path.exists():
            print(f"   ✅ {worker_script} exists")
        else:
            print(f"   ❌ {worker_script} missing")
            all_exist = False
    
    if all_exist:
        print("✅ All worker scripts exist")
        return True
    else:
        print("❌ Some worker scripts missing")
        return False

def test_job_queue_integration():
    """Test job queue integration with orchestrator"""
    print("\nTesting Job Queue Integration...")
    
    try:
        orchestrator = Orchestrator()
        
        # Add various job types
        jobs = [
            orchestrator.job_queue.enqueue(JobType.EVALUATE_TASK, {"epoch": "epoch-001", "task": "task-001"}),
            orchestrator.job_queue.enqueue(JobType.EVALUATE_TASK, {"epoch": "epoch-001", "task": "task-002"}),
            orchestrator.job_queue.enqueue(JobType.COMPILE_CHECK, {"epoch": "epoch-001", "task": "task-001"}),
        ]
        
        print(f"   Added {len(jobs)} test jobs")
        
        # Check queue stats
        stats = orchestrator.job_queue.get_queue_stats()
        print(f"   Queue stats: {stats}")
        
        # Test dequeue
        job = orchestrator.job_queue.dequeue("test-worker")
        if job:
            print(f"   Successfully dequeued job: {job.id[:8]} ({job.job_type.value})")
            
            # Put it back as completed
            from job_queue import JobResult
            result = JobResult(success=True, output="Test completion")
            orchestrator.job_queue.complete_job(job.id, result)
            print(f"   Marked job as completed")
        
        # Final stats
        final_stats = orchestrator.job_queue.get_queue_stats()
        print(f"   Final stats: {final_stats}")
        
        print("✅ Job queue integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Job queue integration test failed: {e}")
        return False

def main():
    """Run orchestrator tests"""
    print("🧪 Testing Orchestrator Components")
    print("=" * 50)
    
    tests = [
        test_orchestrator_basic,
        test_worker_script_existence,
        test_job_queue_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All orchestrator tests passed!")
        return True
    else:
        print("❌ Some orchestrator tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)