#!/usr/bin/env python3
"""
Test evaluate-epoch functionality
"""

import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from evaluate_epoch import EpochEvaluator

def test_epoch_evaluator_setup():
    """Test epoch evaluator task setup functionality"""
    print("Testing Epoch Evaluator Setup...")
    
    try:
        evaluator = EpochEvaluator()
        
        # Test with epoch-001
        epoch_name = "epoch-001"
        
        # Test _setup_tasks method
        print(f"   Testing task setup for {epoch_name}")
        task_names = evaluator._setup_tasks(epoch_name)
        
        print(f"   ✅ Setup {len(task_names)} tasks: {task_names}")
        
        # Verify tasks were copied
        epoch_runs = evaluator.base_dir / "epochs" / epoch_name / "runs"
        
        if not epoch_runs.exists():
            print("   ❌ Epoch runs directory not created")
            return False
        
        # Check each task
        for task_name in task_names:
            task_dir = epoch_runs / task_name
            
            required_items = [
                task_dir / "input" / "TASK.md",
                task_dir / "expected-output",
                task_dir / "tests",
                task_dir / "output"  # Should be created
            ]
            
            for item in required_items:
                if not item.exists():
                    print(f"   ❌ Missing: {item}")
                    return False
            
            print(f"   ✅ {task_name} properly set up")
        
        print("✅ Epoch evaluator setup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Epoch evaluator setup test failed: {e}")
        return False

def test_job_enqueueing():
    """Test job enqueueing functionality"""
    print("\nTesting Job Enqueueing...")
    
    try:
        evaluator = EpochEvaluator()
        
        # Test job enqueueing
        epoch_name = "epoch-001"
        task_names = ["task-001", "task-002"]
        
        job_ids = evaluator._enqueue_evaluation_jobs(epoch_name, task_names, True)
        
        print(f"   ✅ Enqueued {len(job_ids)} jobs")
        
        # Verify jobs are in queue
        for job_id in job_ids:
            job = evaluator.job_queue.get_job(job_id)
            if not job:
                print(f"   ❌ Job {job_id} not found in queue")
                return False
            
            print(f"   ✅ Job {job_id[:8]}... found in queue ({job.parameters['task']})")
        
        print("✅ Job enqueueing test passed")
        return True
        
    except Exception as e:
        print(f"❌ Job enqueueing test failed: {e}")
        return False

def test_summary_generation():
    """Test evaluation summary generation"""
    print("\nTesting Summary Generation...")
    
    try:
        evaluator = EpochEvaluator()
        
        # Create mock job results
        from job_queue import Job, JobType, JobStatus, JobResult
        from datetime import datetime
        
        mock_results = {}
        
        # Successful job
        job1 = Job(
            id="job-001",
            job_type=JobType.EVALUATE_TASK,
            status=JobStatus.COMPLETED,
            parameters={"epoch": "epoch-001", "task": "task-001"},
            created_at=datetime.now()
        )
        job1.result = JobResult(success=True, output="Task completed successfully")
        mock_results["job-001"] = job1
        
        # Failed job
        job2 = Job(
            id="job-002", 
            job_type=JobType.EVALUATE_TASK,
            status=JobStatus.FAILED,
            parameters={"epoch": "epoch-001", "task": "task-002"},
            created_at=datetime.now()
        )
        job2.result = JobResult(success=False, error="API rate limit exceeded")
        mock_results["job-002"] = job2
        
        # Generate summary
        summary = evaluator._generate_evaluation_summary("epoch-001", mock_results)
        
        # Verify summary
        expected_fields = ['epoch', 'total_tasks', 'successful_tasks', 'failed_tasks', 
                          'task_results', 'overall_score', 'max_possible_score', 'success_rate']
        
        for field in expected_fields:
            if field not in summary:
                print(f"   ❌ Missing field in summary: {field}")
                return False
        
        print(f"   ✅ Summary generated with all required fields")
        print(f"   ✅ Success rate: {summary['success_rate']}%")
        print(f"   ✅ Tasks: {summary['successful_tasks']}/{summary['total_tasks']}")
        
        print("✅ Summary generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Summary generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Evaluate Epoch Functionality")
    print("=" * 50)
    
    tests = [
        test_epoch_evaluator_setup,
        test_job_enqueueing,
        test_summary_generation
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
        print("🎉 All evaluate-epoch tests passed!")
        return True
    else:
        print("❌ Some evaluate-epoch tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)