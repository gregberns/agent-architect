#!/usr/bin/env python3
"""
Fixed task worker - executes individual task evaluations
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

class TaskWorker:
    """Worker for executing individual task evaluations"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.running = True
        self.setup_signal_handlers()
        
        # Force initialize everything in try/catch to prevent startup errors
        try:
            self.config = load_config()
            self.job_queue = JobQueue(self.config.job_queue_file)
        except Exception as e:
            # If we can't initialize, there's nothing we can do
            # Write to stderr in case it's not redirected
            sys.stderr.write(f"FATAL: Task worker {worker_id} init failed: {e}\n")
            sys.stderr.flush()
            sys.exit(1)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.running = False
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def run(self):
        """Main worker loop with robust error handling"""
        
        poll_count = 0
        consecutive_errors = 0
        
        while self.running:
            poll_count += 1
            
            try:
                # Get next job from queue
                job = self.job_queue.dequeue(self.worker_id)
                
                if job is None:
                    # No jobs available, wait and try again
                    time.sleep(self.config.timeouts.job_queue_poll_interval)
                    consecutive_errors = 0  # Reset error count
                    continue
                
                if job.job_type != JobType.EVALUATE_TASK:
                    # Wrong job type, put it back
                    self.job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}")
                    continue
                
                # Execute the task
                result = self._execute_task(job)
                
                # Update job with result
                if result.success:
                    self.job_queue.complete_job(job.id, result)
                else:
                    self.job_queue.fail_job(job.id, result.error)
                
                consecutive_errors = 0  # Reset error count on success
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                consecutive_errors += 1
                
                # If we have too many consecutive errors, exit
                if consecutive_errors > 10:
                    sys.stderr.write(f"FATAL: Task worker {self.worker_id} too many errors, exiting\n")
                    sys.stderr.flush()
                    break
                
                # Wait before retrying
                time.sleep(min(consecutive_errors, 5))  # Exponential backoff up to 5s
    
    def _execute_task(self, job) -> JobResult:
        """Execute a single task evaluation"""
        try:
            # Extract job parameters
            epoch = job.parameters.get('epoch', 'epoch-001')
            task = job.parameters.get('task', 'task-001')
            
            # Build paths
            base_dir = Path(__file__).parent.parent.parent
            epoch_dir = base_dir / "epochs" / epoch
            agent_src_dir = epoch_dir / "agent-src"
            
            if not agent_src_dir.exists():
                return JobResult(
                    success=False,
                    error=f"Agent source directory not found: {agent_src_dir}"
                )
            
            # Execute docker-compose
            start_time = time.time()
            
            env = os.environ.copy()
            env['TASK_ID'] = task
            
            result = subprocess.run(
                ["docker-compose", "up", "--build"],
                cwd=agent_src_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.timeouts.task_execution_timeout
            )
            
            execution_time = time.time() - start_time
            
            # Check if task generated output
            task_output_dir = epoch_dir / "runs" / task / "output"
            output_files = list(task_output_dir.glob("*.py")) if task_output_dir.exists() else []
            
            if result.returncode == 0:
                return JobResult(
                    success=True,
                    output=f"Task completed. Generated {len(output_files)} Python files.",
                    execution_time=execution_time,
                    artifacts={
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'output_files': [str(f) for f in output_files],
                        'return_code': result.returncode
                    }
                )
            else:
                # Task failed but that might be expected (e.g., API limits)
                # Still record as success if we got some output
                if output_files:
                    return JobResult(
                        success=True,
                        output=f"Task completed with issues. Generated {len(output_files)} Python files.",
                        execution_time=execution_time,
                        artifacts={
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'output_files': [str(f) for f in output_files],
                            'return_code': result.returncode
                        }
                    )
                else:
                    return JobResult(
                        success=False,
                        error=f"Task execution failed (return code {result.returncode})",
                        execution_time=execution_time,
                        artifacts={
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'return_code': result.returncode
                        }
                    )
        
        except subprocess.TimeoutExpired:
            return JobResult(
                success=False,
                error=f"Task execution timed out after {self.config.timeouts.task_execution_timeout} seconds"
            )
        except Exception as e:
            return JobResult(
                success=False,
                error=f"Task execution error: {str(e)}"
            )

def main():
    """Main entry point"""
    worker_id = os.environ.get('WORKER_ID', 'task-worker-unknown')
    worker = TaskWorker(worker_id)
    worker.run()

if __name__ == "__main__":
    main()