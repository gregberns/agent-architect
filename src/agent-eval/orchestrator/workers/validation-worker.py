#!/usr/bin/env python3
"""
Validation worker - runs compilation checks and tests (placeholder)
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

class ValidationWorker:
    """Worker for executing validation tasks"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.config = load_config()
        self.job_queue = JobQueue(self.config.job_queue_file)
        self.running = True
    
    def run(self):
        """Main worker loop"""
        print(f"Validation worker {self.worker_id} started")
        
        while self.running:
            try:
                # Get next job from queue (only COMPILE_CHECK jobs)
                job = self.job_queue.dequeue(self.worker_id, [JobType.COMPILE_CHECK])
                
                if job is None:
                    # No jobs available, wait and try again
                    time.sleep(self.config.timeouts.job_queue_poll_interval)
                    continue
                
                if job.job_type != JobType.COMPILE_CHECK:
                    # Wrong job type, put it back
                    self.job_queue.fail_job(job.id, f"Wrong job type for validation worker: {job.job_type}")
                    continue
                
                print(f"Worker {self.worker_id} processing validation job {job.id[:8]}...")
                
                # Execute the validation
                result = self._execute_validation(job)
                
                # Update job with result
                if result.success:
                    self.job_queue.complete_job(job.id, result)
                    print(f"Worker {self.worker_id} completed validation job {job.id[:8]} successfully")
                else:
                    self.job_queue.fail_job(job.id, result.error)
                    print(f"Worker {self.worker_id} failed validation job {job.id[:8]}: {result.error}")
                
            except KeyboardInterrupt:
                print(f"Worker {self.worker_id} shutting down...")
                self.running = False
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                time.sleep(5)
    
    def _execute_validation(self, job) -> JobResult:
        """Execute validation checks"""
        try:
            # Extract job parameters
            epoch = job.parameters.get('epoch', 'epoch-001')
            task = job.parameters.get('task', 'task-001')
            
            print(f"  Validating {epoch}/{task}")
            
            # Build paths
            base_dir = Path(__file__).parent.parent.parent
            task_dir = base_dir / "epochs" / epoch / "runs" / task
            output_dir = task_dir / "output"
            tests_dir = task_dir / "tests"
            
            if not output_dir.exists():
                return JobResult(
                    success=False,
                    error=f"Output directory not found: {output_dir}"
                )
            
            # Check for Python files
            py_files = list(output_dir.glob("*.py"))
            if not py_files:
                return JobResult(
                    success=False,
                    error="No Python files found in output directory"
                )
            
            compilation_score = 0
            test_score = 0
            total_files = len(py_files)
            
            # Test compilation for each Python file
            compiled_files = 0
            for py_file in py_files:
                try:
                    # Try to compile the Python file
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        compiled_files += 1
                        print(f"    ✅ {py_file.name} compiles successfully")
                    else:
                        print(f"    ❌ {py_file.name} compilation failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"    ❌ {py_file.name} compilation error: {e}")
            
            # Calculate compilation score (1 point if all files compile)
            if compiled_files == total_files:
                compilation_score = 1
            
            # Run tests if available
            if tests_dir.exists() and list(tests_dir.glob("test_*.py")):
                try:
                    # Run pytest on the tests directory
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", str(tests_dir), "-v"],
                        cwd=str(task_dir),
                        capture_output=True,
                        text=True,
                        timeout=self.config.timeouts.validation_timeout
                    )
                    
                    if result.returncode == 0:
                        test_score = 1
                        print(f"    ✅ Tests passed")
                    else:
                        print(f"    ❌ Tests failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"    ❌ Test execution error: {e}")
            else:
                print(f"    ⚠️  No tests found in {tests_dir}")
            
            total_score = compilation_score + test_score
            
            return JobResult(
                success=True,
                output=f"Validation completed. Score: {total_score}/2 (compilation: {compilation_score}, tests: {test_score})",
                execution_time=1.0,
                artifacts={
                    'compilation_score': compilation_score,
                    'test_score': test_score,
                    'total_score': total_score,
                    'compiled_files': compiled_files,
                    'total_files': total_files,
                    'output_files': [str(f) for f in py_files]
                }
            )
            
        except Exception as e:
            return JobResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )

def main():
    """Main entry point"""
    worker_id = os.environ.get('WORKER_ID', 'validation-worker-unknown')
    worker = ValidationWorker(worker_id)
    worker.run()

if __name__ == "__main__":
    main()