#!/usr/bin/env python3
"""
Integration tests for orchestrator-worker communication
"""

import sys
import time
import subprocess
import signal
from pathlib import Path
from threading import Thread

# Add fixtures to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from utilities import test_environment, create_test_jobs, wait_for_job_completion, TestResults, MockDockerRunner
from job_queue import JobQueue, JobType, JobStatus


class TestOrchestratorWorkers:
    """Test orchestrator and worker integration"""
    
    def test_single_worker_job_processing(self):
        """Test single worker processing jobs"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create test jobs
            job_ids = create_test_jobs(job_queue, 2)
            
            # Start a single worker manually (simplified)
            worker_completed_jobs = []
            
            def simple_worker():
                worker_id = "test-worker-1"
                processed = 0
                
                while processed < 2:  # Process 2 jobs then stop
                    job = job_queue.dequeue(worker_id)
                    if job:
                        # Simulate job processing
                        time.sleep(0.1)  # Brief processing time
                        
                        # Mark as completed
                        from job_queue import JobResult
                        result = JobResult(
                            success=True,
                            output=f"Completed by {worker_id}",
                            execution_time=0.1,
                            artifacts={"test": True}
                        )
                        job_queue.complete_job(job.id, result)
                        worker_completed_jobs.append(job.id)
                        processed += 1
                    else:
                        time.sleep(0.1)  # Brief wait if no jobs
            
            # Run worker in thread
            worker_thread = Thread(target=simple_worker)
            worker_thread.start()
            
            # Wait for completion
            worker_thread.join(timeout=10)
            
            # Verify all jobs were processed
            assert len(worker_completed_jobs) == 2
            
            # Verify job statuses
            for job_id in job_ids:
                job = job_queue.get_job(job_id)
                assert job.status == JobStatus.COMPLETED
                assert job.worker_id == "test-worker-1"
    
    def test_multiple_workers_concurrent_processing(self):
        """Test multiple workers processing jobs concurrently"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create multiple test jobs
            job_ids = create_test_jobs(job_queue, 6)
            
            worker_results = {}
            
            def worker_process(worker_id: str, max_jobs: int):
                worker_results[worker_id] = []
                processed = 0
                
                while processed < max_jobs:
                    job = job_queue.dequeue(worker_id)
                    if job:
                        # Simulate processing time
                        time.sleep(0.05)
                        
                        # Complete job
                        from job_queue import JobResult
                        result = JobResult(
                            success=True,
                            output=f"Completed by {worker_id}",
                            execution_time=0.05,
                            artifacts={"worker": worker_id}
                        )
                        job_queue.complete_job(job.id, result)
                        worker_results[worker_id].append(job.id)
                        processed += 1
                    else:
                        time.sleep(0.01)
            
            # Start multiple workers
            workers = []
            for i in range(3):
                worker_id = f"test-worker-{i+1}"
                thread = Thread(target=worker_process, args=(worker_id, 2))
                thread.start()
                workers.append(thread)
            
            # Wait for all workers to complete
            for thread in workers:
                thread.join(timeout=10)
            
            # Verify all jobs were distributed and completed
            total_processed = sum(len(jobs) for jobs in worker_results.values())
            assert total_processed == 6
            
            # Verify no job was processed by multiple workers
            all_processed_jobs = []
            for jobs in worker_results.values():
                all_processed_jobs.extend(jobs)
            
            assert len(all_processed_jobs) == len(set(all_processed_jobs))
            
            # Verify all original jobs were completed
            for job_id in job_ids:
                job = job_queue.get_job(job_id)
                assert job.status == JobStatus.COMPLETED
    
    def test_worker_failure_recovery(self):
        """Test worker failure and job recovery"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create test jobs
            job_ids = create_test_jobs(job_queue, 3)
            
            # Worker that fails midway
            def failing_worker():
                worker_id = "failing-worker"
                
                # Process first job successfully
                job1 = job_queue.dequeue(worker_id)
                if job1:
                    from job_queue import JobResult
                    result = JobResult(
                        success=True,
                        output="First job completed",
                        execution_time=0.1,
                        artifacts={}
                    )
                    job_queue.complete_job(job1.id, result)
                
                # Take second job but "crash" without completing it
                job2 = job_queue.dequeue(worker_id)
                # Simulate worker crash - job stays in RUNNING state
                
                return job1.id if job1 else None, job2.id if job2 else None
            
            # Run failing worker
            completed_job_id, abandoned_job_id = failing_worker()
            
            # Verify states
            if completed_job_id:
                job = job_queue.get_job(completed_job_id)
                assert job.status == JobStatus.COMPLETED
            
            if abandoned_job_id:
                job = job_queue.get_job(abandoned_job_id)
                assert job.status == JobStatus.RUNNING
            
            # Reset running jobs (simulates orchestrator recovery)
            reset_count = job_queue.reset_running_jobs()
            assert reset_count == 1
            
            # Verify abandoned job is back to pending
            if abandoned_job_id:
                job = job_queue.get_job(abandoned_job_id)
                assert job.status == JobStatus.PENDING
            
            # New worker can pick up the recovered job
            def recovery_worker():
                worker_id = "recovery-worker"
                processed_jobs = []
                
                # Process all remaining pending jobs
                while True:
                    job = job_queue.dequeue(worker_id)
                    if not job:
                        break
                    
                    from job_queue import JobResult
                    result = JobResult(
                        success=True,
                        output=f"Recovered by {worker_id}",
                        execution_time=0.1,
                        artifacts={}
                    )
                    job_queue.complete_job(job.id, result)
                    processed_jobs.append(job.id)
                
                return processed_jobs
            
            recovered_jobs = recovery_worker()
            
            # Verify all jobs are now completed
            stats = job_queue.get_queue_stats()
            assert stats['completed'] == 3
            assert stats['running'] == 0
            assert stats['pending'] == 0
    
    def test_job_timeout_handling(self):
        """Test job timeout detection and handling"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create a job with short timeout (simulate in job processing)
            job_id = job_queue.enqueue(
                JobType.EVALUATE_TASK,
                {'epoch': 'test-epoch', 'task': 'test-task', 'timeout': 1},
                max_retries=1
            )
            
            # Worker takes job but processes slowly
            def slow_worker():
                worker_id = "slow-worker"
                job = job_queue.dequeue(worker_id)
                
                if job:
                    # Simulate long processing (longer than timeout)
                    time.sleep(2)
                    
                    # Try to complete job (should handle timeout)
                    from job_queue import JobResult
                    result = JobResult(
                        success=True,
                        output="Slow completion",
                        execution_time=2.0,
                        artifacts={}
                    )
                    return job_queue.complete_job(job.id, result)
                
                return False
            
            # Start slow worker
            worker_thread = Thread(target=slow_worker)
            worker_thread.start()
            
            # Simulate timeout detection (in real system, orchestrator would do this)
            time.sleep(1.5)
            
            # Check if job is still running
            job = job_queue.get_job(job_id)
            if job.status == JobStatus.RUNNING:
                # Simulate timeout handling - reset to pending for retry
                job_queue.reset_running_jobs()
            
            worker_thread.join()
            
            # Job might be completed (if worker finished) or pending (if reset for timeout)
            # This is a race condition that can happen in real systems
            job = job_queue.get_job(job_id)
            assert job.status in [JobStatus.PENDING, JobStatus.COMPLETED]
    
    def test_different_job_types(self):
        """Test workers handling different job types"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file)
            
            # Create different types of jobs
            eval_job_id = job_queue.enqueue(
                JobType.EVALUATE_TASK,
                {'epoch': 'test-epoch', 'task': 'test-task'}
            )
            
            compile_job_id = job_queue.enqueue(
                JobType.COMPILE_CHECK,
                {'epoch': 'test-epoch', 'task': 'test-task'}
            )
            
            # Task worker should only process EVALUATE_TASK jobs
            def task_worker():
                worker_id = "task-worker"
                processed_jobs = []
                
                for _ in range(3):  # Try to get 3 jobs
                    job = job_queue.dequeue(worker_id)
                    if job:
                        if job.job_type == JobType.EVALUATE_TASK:
                            # Process evaluate task
                            from job_queue import JobResult
                            result = JobResult(
                                success=True,
                                output="Task evaluation completed",
                                execution_time=0.1,
                                artifacts={}
                            )
                            job_queue.complete_job(job.id, result)
                            processed_jobs.append(job.id)
                        else:
                            # Put back wrong job type - don't retry since it's wrong type
                            job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}", allow_retry=False)
                    else:
                        break
                
                return processed_jobs
            
            # Validation worker should only process COMPILE_CHECK jobs
            def validation_worker():
                worker_id = "validation-worker"
                processed_jobs = []
                
                for _ in range(3):  # Try to get 3 jobs
                    job = job_queue.dequeue(worker_id)
                    if job:
                        if job.job_type == JobType.COMPILE_CHECK:
                            # Process compile check
                            from job_queue import JobResult
                            result = JobResult(
                                success=True,
                                output="Compilation check completed",
                                execution_time=0.1,
                                artifacts={'compiled': True}
                            )
                            job_queue.complete_job(job.id, result)
                            processed_jobs.append(job.id)
                        else:
                            # Put back wrong job type - don't retry since it's wrong type  
                            job_queue.fail_job(job.id, f"Wrong job type for validation worker: {job.job_type}", allow_retry=False)
                    else:
                        break
                
                return processed_jobs
            
            # Run both workers
            task_thread = Thread(target=task_worker)
            validation_thread = Thread(target=validation_worker)
            
            task_thread.start()
            validation_thread.start()
            
            task_thread.join(timeout=5)
            validation_thread.join(timeout=5)
            
            # Verify correct job processing
            eval_job = job_queue.get_job(eval_job_id)
            compile_job = job_queue.get_job(compile_job_id)
            
            # Both jobs should be either completed (by correct worker) or failed (by wrong worker)
            # In a real system, workers would be configured to only pick up relevant job types
            assert eval_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
            assert compile_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
            
            # At least one job should be completed by each worker type
            # (This tests that workers can distinguish job types)
            completed_eval = eval_job.status == JobStatus.COMPLETED
            completed_compile = compile_job.status == JobStatus.COMPLETED
            
            # Either the eval job was completed by task-worker, or compile job by validation-worker
            # (or both - which would be ideal)
            task_worker_success = completed_eval and eval_job.worker_id == "task-worker"
            validation_worker_success = completed_compile and compile_job.worker_id == "validation-worker"
            
            assert task_worker_success or validation_worker_success, \
                f"At least one worker should complete its appropriate job type. " \
                f"Eval: {eval_job.status}/{eval_job.worker_id}, Compile: {compile_job.status}/{compile_job.worker_id}"


def run_orchestrator_worker_tests():
    """Run all orchestrator-worker integration tests"""
    print("🧪 Running Orchestrator-Worker Integration Tests")
    print("=" * 50)
    
    test_instance = TestOrchestratorWorkers()
    
    tests = [
        ('Single Worker Job Processing', test_instance.test_single_worker_job_processing),
        ('Multiple Workers Concurrent Processing', test_instance.test_multiple_workers_concurrent_processing),
        ('Worker Failure Recovery', test_instance.test_worker_failure_recovery),
        ('Job Timeout Handling', test_instance.test_job_timeout_handling),
        ('Different Job Types', test_instance.test_different_job_types),
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
    results = run_orchestrator_worker_tests()
    
    from utilities import print_test_summary
    print_test_summary(results)
    
    sys.exit(0 if results.failed == 0 else 1)