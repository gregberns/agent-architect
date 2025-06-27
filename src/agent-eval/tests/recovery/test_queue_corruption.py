#!/usr/bin/env python3
"""
Recovery tests for queue corruption handling
"""

import sys
import json
import time
from pathlib import Path

# Add fixtures to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from utilities import test_environment, create_corrupted_queue_file, TestResults
from job_queue import JobQueue, JobType, JobStatus


class TestQueueCorruption:
    """Test queue corruption detection and recovery"""
    
    def test_invalid_json_recovery(self):
        """Test recovery from invalid JSON in queue file"""
        with test_environment() as env:
            # Create valid queue first
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Add some jobs
            job_id1 = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'test1'})
            job_id2 = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'test2'})
            
            # Corrupt the queue file
            create_corrupted_queue_file(env.queue_file, "invalid_json")
            
            # Try to create new queue instance - should handle corruption
            try:
                corrupted_queue = JobQueue(env.queue_file, silent=True)
                
                # Should start with empty queue after corruption recovery
                stats = corrupted_queue.get_queue_stats()
                assert stats['pending'] == 0
                assert stats['running'] == 0
                assert stats['completed'] == 0
                assert stats['failed'] == 0
                
                # Should be able to add new jobs
                new_job_id = corrupted_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'recovered'})
                assert new_job_id is not None
                
                stats = corrupted_queue.get_queue_stats()
                assert stats['pending'] == 1
                
            except Exception as e:
                # If queue can't recover, at least it should fail gracefully
                assert "JSON" in str(e) or "corrupt" in str(e).lower()
    
    def test_empty_file_recovery(self):
        """Test recovery from empty queue file"""
        with test_environment() as env:
            # Create empty file
            create_corrupted_queue_file(env.queue_file, "empty_file")
            
            # Should be able to initialize queue
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Should start with empty stats
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 0
            
            # Should be able to add jobs
            job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'test'})
            assert job_id is not None
            
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 1
    
    def test_missing_jobs_key_recovery(self):
        """Test recovery from missing jobs key in JSON"""
        with test_environment() as env:
            # Create file with missing jobs key
            create_corrupted_queue_file(env.queue_file, "missing_jobs_key")
            
            # Should be able to initialize queue
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Should start with empty stats
            stats = job_queue.get_queue_stats()
            assert stats['pending'] == 0
            
            # Should be able to add jobs
            job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'test'})
            assert job_id is not None
    
    def test_truncated_file_recovery(self):
        """Test recovery from truncated JSON file"""
        with test_environment() as env:
            # Create truncated file
            create_corrupted_queue_file(env.queue_file, "truncated")
            
            # Should handle truncated JSON
            try:
                job_queue = JobQueue(env.queue_file, silent=True)
                
                # Should start fresh
                stats = job_queue.get_queue_stats()
                assert stats['pending'] == 0
                
                # Should be able to add jobs
                job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'test'})
                assert job_id is not None
                
            except Exception as e:
                # Should fail gracefully with JSON error
                assert "JSON" in str(e) or "corrupt" in str(e).lower()
    
    def test_backup_and_restore(self):
        """Test backup creation and restoration"""
        with test_environment() as env:
            # Create queue with jobs
            job_queue = JobQueue(env.queue_file, silent=True)
            
            original_jobs = []
            for i in range(3):
                job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': f'test{i}'})
                original_jobs.append(job_id)
            
            # Process one job
            job = job_queue.dequeue("test-worker")
            from job_queue import JobResult
            result = JobResult(success=True, output="test", execution_time=1.0)
            job_queue.complete_job(job.id, result)
            
            original_stats = job_queue.get_queue_stats()
            
            # Create backup manually (simulate what recovery system would do)
            backup_file = env.queue_file.with_suffix('.backup')
            with open(env.queue_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
            
            # Corrupt the main file
            create_corrupted_queue_file(env.queue_file, "invalid_json")
            
            # Restore from backup
            with open(backup_file, 'r') as src, open(env.queue_file, 'w') as dst:
                dst.write(src.read())
            
            # Verify restoration
            restored_queue = JobQueue(env.queue_file, silent=True)
            restored_stats = restored_queue.get_queue_stats()
            
            assert restored_stats == original_stats
            
            # Verify specific jobs still exist
            for job_id in original_jobs:
                job = restored_queue.get_job(job_id)
                assert job is not None
    
    def test_concurrent_corruption_handling(self):
        """Test handling corruption during concurrent access"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Add initial jobs
            for i in range(5):
                job_queue.enqueue(JobType.EVALUATE_TASK, {'task': f'test{i}'})
            
            # Simulate concurrent operations
            def worker_operations():
                try:
                    # Try to dequeue jobs
                    for _ in range(3):
                        job = job_queue.dequeue("concurrent-worker")
                        if job:
                            # Brief processing
                            time.sleep(0.01)
                            from job_queue import JobResult
                            result = JobResult(success=True, output="test", execution_time=0.01)
                            job_queue.complete_job(job.id, result)
                except Exception:
                    # Expect some operations to fail due to corruption
                    pass
            
            from threading import Thread
            
            # Start worker
            worker_thread = Thread(target=worker_operations)
            worker_thread.start()
            
            # Corrupt file during operations
            time.sleep(0.005)  # Let worker start
            create_corrupted_queue_file(env.queue_file, "invalid_json")
            
            worker_thread.join(timeout=2)
            
            # System should either recover or fail gracefully
            try:
                # Try to create new queue instance
                new_queue = JobQueue(env.queue_file, silent=True)
                stats = new_queue.get_queue_stats()
                # Should be able to get stats (even if empty after recovery)
                assert isinstance(stats['pending'], int)
            except Exception as e:
                # If can't recover, should be a clear error
                assert "JSON" in str(e) or "corrupt" in str(e).lower() or "permission" in str(e).lower()
    
    def test_gradual_corruption_detection(self):
        """Test detection of gradual corruption in queue data"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Add jobs
            job_ids = []
            for i in range(5):
                job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': f'test{i}'})
                job_ids.append(job_id)
            
            # Manually corrupt job data in the JSON
            with open(env.queue_file, 'r') as f:
                data = json.load(f)
            
            # Corrupt one job's data
            if data.get('jobs'):
                first_job_id = list(data['jobs'].keys())[0]
                data['jobs'][first_job_id]['status'] = "INVALID_STATUS"
            
            with open(env.queue_file, 'w') as f:
                json.dump(data, f)
            
            # Try to load queue - should handle invalid job data
            try:
                corrupted_queue = JobQueue(env.queue_file, silent=True)
                
                # Should be able to get stats
                stats = corrupted_queue.get_queue_stats()
                
                # May have fewer jobs due to corruption filtering
                assert stats['pending'] >= 0
                
                # Should be able to add new jobs
                new_job_id = corrupted_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'new'})
                assert new_job_id is not None
                
            except Exception as e:
                # Should fail with descriptive error
                assert "status" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_recovery_preserves_good_data(self):
        """Test that recovery preserves good data when possible"""
        with test_environment() as env:
            job_queue = JobQueue(env.queue_file, silent=True)
            
            # Create mix of jobs in different states
            # Create all jobs first, then process them in specific order
            pending_job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'pending'})
            running_job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'running'})  
            completed_job_id = job_queue.enqueue(JobType.EVALUATE_TASK, {'task': 'completed'})
            
            # Make one job running (dequeue it but don't complete)
            running_job = job_queue.dequeue("test-worker")
            actual_running_job_id = running_job.id if running_job else None
            
            # Complete a different job
            completed_job = job_queue.dequeue("test-worker")  
            from job_queue import JobResult
            result = JobResult(success=True, output="test", execution_time=1.0)
            job_queue.complete_job(completed_job.id, result)
            
            # Find the remaining pending job
            remaining_jobs = [job_id for job_id in [pending_job_id, running_job_id, completed_job_id] 
                            if job_id not in [actual_running_job_id, completed_job.id]]
            actual_pending_job_id = remaining_jobs[0] if remaining_jobs else None
            
            original_stats = job_queue.get_queue_stats()
            
            # Now partially corrupt the file (corrupt just one job)
            with open(env.queue_file, 'r') as f:
                data = json.load(f)
            
            # Corrupt the running job but leave others intact
            if data.get('jobs') and actual_running_job_id and actual_running_job_id in data['jobs']:
                data['jobs'][actual_running_job_id] = {"corrupted": True}
            
            with open(env.queue_file, 'w') as f:
                json.dump(data, f)
            
            # Load queue with partial corruption
            recovered_queue = JobQueue(env.queue_file, silent=True)
            
            # Should preserve good jobs
            pending_job_recovered = recovered_queue.get_job(actual_pending_job_id) if actual_pending_job_id else None
            completed_job_recovered = recovered_queue.get_job(completed_job.id)
            
            # Good jobs should still exist
            assert pending_job_recovered is not None, f"Pending job {actual_pending_job_id} should be preserved"
            assert completed_job_recovered is not None, f"Completed job {completed_job.id} should be preserved"
            
            # Corrupted job may be missing or reset
            running_job_recovered = recovered_queue.get_job(actual_running_job_id) if actual_running_job_id else None
            # Either missing (filtered out) or reset to pending
            if running_job_recovered:
                assert running_job_recovered.status in [JobStatus.PENDING, JobStatus.FAILED]


def run_queue_corruption_tests():
    """Run all queue corruption recovery tests"""
    print("🧪 Running Queue Corruption Recovery Tests")
    print("=" * 50)
    
    test_instance = TestQueueCorruption()
    
    tests = [
        ('Invalid JSON Recovery', test_instance.test_invalid_json_recovery),
        ('Empty File Recovery', test_instance.test_empty_file_recovery),
        ('Missing Jobs Key Recovery', test_instance.test_missing_jobs_key_recovery),
        ('Truncated File Recovery', test_instance.test_truncated_file_recovery),
        ('Backup and Restore', test_instance.test_backup_and_restore),
        ('Concurrent Corruption Handling', test_instance.test_concurrent_corruption_handling),
        ('Gradual Corruption Detection', test_instance.test_gradual_corruption_detection),
        ('Recovery Preserves Good Data', test_instance.test_recovery_preserves_good_data),
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
            import traceback
            errors.append(f"{test_name}: {e}\n{traceback.format_exc()}")
            failed += 1
    
    execution_time = time.time() - start_time
    
    return TestResults(
        passed=passed,
        failed=failed,
        errors=errors,
        execution_time=execution_time
    )


if __name__ == "__main__":
    results = run_queue_corruption_tests()
    
    from utilities import print_test_summary
    print_test_summary(results)
    
    sys.exit(0 if results.failed == 0 else 1)