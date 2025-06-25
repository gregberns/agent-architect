#!/usr/bin/env python3
"""
Unit tests for the job queue system
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add fixtures to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from utilities import test_environment, create_test_jobs, simulate_job_completion, assert_job_state, TestResults
from job_queue import JobQueue, JobType, JobStatus, Job, JobResult


class TestJobQueue:
    """Test job queue core functionality"""
    
    def test_basic_enqueue_dequeue(self):
        """Test basic job enqueue and dequeue operations"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Test enqueuing a job
            job_id = job_queue.enqueue(
                JobType.EVALUATE_TASK,
                {'epoch': 'test-epoch', 'task': 'test-task'},
                max_retries=2
            )
            
            assert job_id is not None
            assert len(job_id) > 0
            
            # Test getting the job
            job = job_queue.get_job(job_id)
            assert job is not None
            assert job.job_type == JobType.EVALUATE_TASK
            assert job.status == JobStatus.PENDING
            assert job.parameters['epoch'] == 'test-epoch'
            assert job.parameters['task'] == 'test-task'
            assert job.max_retries == 2
            
            # Test dequeuing the job
            dequeued_job = job_queue.dequeue("test-worker")
            assert dequeued_job is not None
            assert dequeued_job.id == job_id
            assert dequeued_job.status == JobStatus.RUNNING
            assert dequeued_job.worker_id == "test-worker"
    
    def test_queue_statistics(self):
        """Test queue statistics calculation"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Initially empty
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 0
            assert stats['running'] == 0
            assert stats['completed'] == 0
            assert stats['failed'] == 0
            
            # Add some jobs
            job_ids = create_test_jobs(job_queue, 5)
            
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 5
            assert stats['running'] == 0
            assert stats['completed'] == 0
            assert stats['failed'] == 0
            
            # Process some jobs
            job1 = job_queue.dequeue("worker1")
            job2 = job_queue.dequeue("worker2")
            
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 3
            assert stats['running'] == 2
            assert stats['completed'] == 0
            assert stats['failed'] == 0
            
            # Complete one job and fail another (with no retries to ensure it stays failed)
            simulate_job_completion(job_queue, job1.id, success=True)
            
            # For the failure test, we need to exhaust retries or use no retries
            # Let's modify the job to have no retries before failing it
            job2_obj = job_queue.get_job(job2.id)
            job2_obj.max_retries = 0
            simulate_job_completion(job_queue, job2.id, success=False)
            
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 3
            assert stats['running'] == 0
            assert stats['completed'] == 1
            assert stats['failed'] == 1
    
    def test_job_state_transitions(self):
        """Test job state transitions"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create a job
            job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'test': 'data'})
            assert_job_state(job_queue, job_id, JobStatus.PENDING)
            
            # Dequeue (PENDING → RUNNING)
            job = job_queue.dequeue("test-worker")
            assert job.id == job_id
            assert_job_state(job_queue, job_id, JobStatus.RUNNING)
            
            # Complete (RUNNING → COMPLETED)
            result = JobResult(
                success=True,
                output="Test completed",
                execution_time=1.5,
                artifacts={'test': True}
            )
            job_queue.complete_job(job_id, result)
            assert_job_state(job_queue, job_id, JobStatus.COMPLETED)
            
            # Test failure path - create job with no retries to ensure it fails
            job_id2 = job_queue.enqueue(JobType.EVALUATE_TASK, {'test': 'data2'}, max_retries=0)
            job2 = job_queue.dequeue("test-worker")
            
            # Fail (RUNNING → FAILED)
            job_queue.fail_job(job_id2, "Test failure")
            assert_job_state(job_queue, job_id2, JobStatus.FAILED)
    
    def test_worker_assignment(self):
        """Test worker assignment and tracking"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create jobs
            job_ids = create_test_jobs(job_queue, 3)
            
            # Assign to different workers
            job1 = job_queue.dequeue("worker-1")
            job2 = job_queue.dequeue("worker-2")
            job3 = job_queue.dequeue("worker-1")  # Same worker gets another job
            
            assert job1.worker_id == "worker-1"
            assert job2.worker_id == "worker-2"
            assert job3.worker_id == "worker-1"
            
            # Test that no more jobs are available
            job_none = job_queue.dequeue("worker-3")
            assert job_none is None
    
    def test_job_retry_logic(self):
        """Test job retry logic"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create job with 2 retries allowed
            job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'test': 'retry'}, max_retries=2)
            
            # First attempt
            job = job_queue.dequeue("worker-1")
            job_queue.fail_job(job_id, "First failure")
            
            job = job_queue.get_job(job_id)
            assert job.status == JobStatus.PENDING  # Should be back to pending for retry
            assert job.retry_count == 1
            
            # Second attempt  
            job = job_queue.dequeue("worker-1")
            job_queue.fail_job(job_id, "Second failure")
            
            job = job_queue.get_job(job_id)
            assert job.status == JobStatus.PENDING  # Still pending, one retry left
            assert job.retry_count == 2
            
            # Third attempt (final)
            job = job_queue.dequeue("worker-1")
            job_queue.fail_job(job_id, "Final failure")
            
            job = job_queue.get_job(job_id)
            assert job.status == JobStatus.FAILED  # Now permanently failed
            assert job.retry_count == 2  # Retries maxed out
    
    def test_job_persistence(self):
        """Test job queue persistence"""
        with test_environment() as env:
            # Create jobs with first queue instance
            job_queue1 = JobQueue(env.queue_file)
            job_ids = create_test_jobs(job_queue1, 3)
            
            # Process one job
            job = job_queue1.dequeue("worker-1")
            simulate_job_completion(job_queue1, job.id, success=True)
            
            # Create new queue instance and verify persistence
            job_queue2 = JobQueue(env.queue_file)
            
            stats1 = job_queue1.get_queue_stats()
            stats2 = job_queue2.get_queue_stats()
            
            assert stats1 == stats2
            assert stats2['pending'] == 2
            assert stats2['completed'] == 1
            
            # Verify job details persist
            for job_id in job_ids:
                job1 = job_queue1.get_job(job_id)
                job2 = job_queue2.get_job(job_id)
                assert job1.id == job2.id
                assert job1.status == job2.status
    
    def test_concurrent_access(self):
        """Test concurrent queue access safety"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create jobs
            job_ids = create_test_jobs(job_queue, 5)
            
            # Simulate concurrent dequeue operations
            jobs_dequeued = []
            for i in range(3):
                job = job_queue.dequeue(f"worker-{i}")
                if job:
                    jobs_dequeued.append(job)
            
            # Should have dequeued exactly 3 jobs
            assert len(jobs_dequeued) == 3
            
            # All should be different jobs
            job_ids_dequeued = [job.id for job in jobs_dequeued]
            assert len(set(job_ids_dequeued)) == 3
            
            # All should be in RUNNING state
            for job in jobs_dequeued:
                assert_job_state(job_queue, job.id, JobStatus.RUNNING)
    
    def test_queue_cleanup_operations(self):
        """Test queue cleanup operations"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create and process various jobs
            job_ids = create_test_jobs(job_queue, 5)
            
            # Complete some jobs
            for i in range(3):
                job = job_queue.dequeue(f"worker-{i}")
                simulate_job_completion(job_queue, job.id, success=True)
            
            # Reset running jobs
            running_reset = job_queue.reset_running_jobs()
            assert running_reset == 0  # No running jobs to reset
            
            # Clear completed jobs (use very short duration to clear recent jobs)
            from datetime import timedelta
            cleared = job_queue.clear_completed_jobs(older_than=timedelta(seconds=0))
            assert cleared == 3
            
            stats = job_queue.get_queue_stats()
            assert stats['completed'] == 0
            assert stats['pending'] == 2
            
            # Clear all jobs
            total_cleared = job_queue.clear_all_jobs()
            assert total_cleared == 2
            
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 0
            assert stats['running'] == 0
            assert stats['completed'] == 0
            assert stats['failed'] == 0
    
    def test_invalid_operations(self):
        """Test handling of invalid operations"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Test getting non-existent job
            job = job_queue.get_job("non-existent-id")
            assert job is None
            
            # Test completing non-existent job
            result = JobResult(success=True, output="test", execution_time=1.0)
            success = job_queue.complete_job("non-existent-id", result)
            assert not success
            
            # Test failing non-existent job
            success = job_queue.fail_job("non-existent-id", "error")
            assert not success
            
            # Test dequeue with no jobs
            job = job_queue.dequeue("worker-1")
            assert job is None


def run_job_queue_tests():
    """Run all job queue tests"""
    print("🧪 Running Job Queue Unit Tests")
    print("=" * 50)
    
    test_instance = TestJobQueue()
    
    tests = [
        ('Basic Enqueue/Dequeue', test_instance.test_basic_enqueue_dequeue),
        ('Queue Statistics', test_instance.test_queue_statistics),
        ('Job State Transitions', test_instance.test_job_state_transitions),
        ('Worker Assignment', test_instance.test_worker_assignment),
        ('Job Retry Logic', test_instance.test_job_retry_logic),
        ('Job Persistence', test_instance.test_job_persistence),
        ('Concurrent Access', test_instance.test_concurrent_access),
        ('Queue Cleanup Operations', test_instance.test_queue_cleanup_operations),
        ('Invalid Operations', test_instance.test_invalid_operations),
    ]
    
    passed = 0
    failed = 0
    errors = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            print(f"  Running: {test_name}... ", end="")
            test_func()
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            errors.append(f"{test_name}: {e}")
            failed += 1
    
    execution_time = time.time() - start_time
    
    return TestResults(
        passed=passed,
        failed=failed,
        errors=errors,
        execution_time=execution_time
    )


if __name__ == "__main__":
    results = run_job_queue_tests()
    
    from utilities import print_test_summary
    print_test_summary(results)
    
    sys.exit(0 if results.failed == 0 else 1)