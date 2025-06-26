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
        
        # Use runtime paths for job queue file
        agent_eval_root = Path(__file__).parent.parent.parent  # Go up to agent-eval root
        runtime_paths = self.config.get_runtime_paths(agent_eval_root)
        job_queue_path = runtime_paths['state'] / self.config.job_queue_file
        
        self.job_queue = JobQueue(str(job_queue_path))
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
        """Execute validation checks using docker-compose"""
        try:
            # Extract job parameters
            epoch = job.parameters.get('epoch', 'epoch-001')
            task = job.parameters.get('task', 'task-001')
            
            print(f"  Validating {epoch}/{task} using Docker")
            
            # Build paths
            base_dir = Path(__file__).parent.parent.parent
            epoch_dir = base_dir / "epochs" / epoch
            agent_src_dir = epoch_dir / "agent-src"
            task_dir = epoch_dir / "runs" / task
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
            
            # Set environment for docker-compose
            env = os.environ.copy()
            env['TASK_ID'] = task
            
            # Use unique project name to avoid container conflicts
            project_name = f"validation-{epoch}-{task}-{int(time.time())}"
            
            start_time = time.time()
            
            # Step 1: Test compilation using docker-compose
            print(f"    🔍 Testing compilation for {total_files} Python files...")
            
            # Create a shell command to compile all Python files
            py_file_paths = [f"/app/workspace/output/{f.name}" for f in py_files]
            
            compile_stdout = ""
            compile_stderr = ""
            
            try:
                # Use the predefined entrypoint from docker-compose.yml (sh)
                compile_result = subprocess.run(
                    ["docker-compose", "-p", project_name, "run", "--rm",
                     "validation-compile", "-c", 
                     f"python -m py_compile {' '.join(py_file_paths)}"],
                    cwd=agent_src_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                compile_stdout = compile_result.stdout
                compile_stderr = compile_result.stderr
                
                print(f"    🔍 Compilation result: return_code={compile_result.returncode}")
                if compile_result.stdout:
                    print(f"    📤 STDOUT: {compile_result.stdout[:200]}...")
                if compile_result.stderr and "warning" not in compile_result.stderr.lower():
                    print(f"    📤 STDERR: {compile_result.stderr[:200]}...")
                
                if compile_result.returncode == 0:
                    compilation_score = 1
                    print(f"    ✅ All {total_files} files compile successfully")
                else:
                    print(f"    ❌ Compilation failed with return code {compile_result.returncode}")
                    
            except subprocess.TimeoutExpired:
                print(f"    ❌ Compilation timed out after 60 seconds")
                compile_stderr = "Compilation timeout"
            except Exception as e:
                print(f"    ❌ Compilation error: {e}")
                compile_stderr = str(e)
            
            # Step 2: Run tests using docker-compose
            test_stdout = ""
            test_stderr = ""
            
            if tests_dir.exists() and list(tests_dir.glob("test_*.py")):
                print(f"    🧪 Running tests...")
                
                try:
                    test_result = subprocess.run(
                        ["docker-compose", "-p", project_name, "run", "--rm", "validation-test"],
                        cwd=agent_src_dir,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=self.config.timeouts.validation_timeout
                    )
                    
                    test_stdout = test_result.stdout
                    test_stderr = test_result.stderr
                    
                    print(f"    🧪 Test result: return_code={test_result.returncode}")
                    if test_result.stdout:
                        print(f"    📤 TEST STDOUT: {test_result.stdout[:300]}...")
                    if test_result.stderr:
                        print(f"    📤 TEST STDERR: {test_result.stderr[:300]}...")
                    
                    if test_result.returncode == 0:
                        test_score = 1
                        print(f"    ✅ All tests passed")
                    else:
                        print(f"    ❌ Tests failed with return code {test_result.returncode}")
                        
                except subprocess.TimeoutExpired:
                    print(f"    ❌ Tests timed out after {self.config.timeouts.validation_timeout} seconds")
                    test_stderr = "Test timeout"
                except Exception as e:
                    print(f"    ❌ Test execution error: {e}")
                    test_stderr = str(e)
            else:
                print(f"    ⚠️  No tests found in {tests_dir}")
                test_stderr = f"No tests found in {tests_dir}"
            
            execution_time = time.time() - start_time
            total_score = compilation_score + test_score
            
            return JobResult(
                success=True,
                output=f"Docker validation completed. Score: {total_score}/2 (compilation: {compilation_score}, tests: {test_score})",
                execution_time=execution_time,
                artifacts={
                    'compilation_score': compilation_score,
                    'test_score': test_score,
                    'total_score': total_score,
                    'total_files': total_files,
                    'output_files': [str(f) for f in py_files],
                    'validation_method': 'docker-compose',
                    'execution_time': execution_time,
                    'compile_stdout': compile_stdout,
                    'compile_stderr': compile_stderr,
                    'test_stdout': test_stdout,
                    'test_stderr': test_stderr
                }
            )
            
        except Exception as e:
            return JobResult(
                success=False,
                error=f"Docker validation error: {str(e)}"
            )

def main():
    """Main entry point"""
    worker_id = os.environ.get('WORKER_ID', 'validation-worker-unknown')
    worker = ValidationWorker(worker_id)
    worker.run()

if __name__ == "__main__":
    main()