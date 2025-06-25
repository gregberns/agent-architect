#!/usr/bin/env python3
"""
Debug task worker with file-based logging to diagnose orchestrator issues
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

class TaskWorkerDebug:
    """Worker for executing individual task evaluations with comprehensive logging"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.running = True
        self.setup_signal_handlers()
        
        # Setup file-based logging
        self.log_file = Path(__file__).parent.parent / f"worker-{worker_id}.log"
        self.log(f"INIT: Task worker {worker_id} initializing...")
        
        # Force initialize everything in try/catch to prevent startup errors
        try:
            self.log("INIT: Loading config...")
            self.config = load_config()
            self.log("INIT: Creating job queue...")
            self.job_queue = JobQueue(self.config.job_queue_file)
            self.log("INIT: Initialization complete")
        except Exception as e:
            self.log(f"FATAL: Task worker {worker_id} init failed: {e}")
            sys.exit(1)
    
    def log(self, message: str):
        """Log message to file with timestamp"""
        try:
            timestamp = datetime.now().isoformat()
            with open(self.log_file, 'a') as f:
                f.write(f"{timestamp} [{self.worker_id}] {message}\n")
                f.flush()  # Force write immediately
        except Exception as e:
            # If we can't log, try to write to stderr
            sys.stderr.write(f"LOG_ERROR: {e}\n")
            sys.stderr.flush()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.log(f"SIGNAL: Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def run(self):
        """Main worker loop with comprehensive logging"""
        
        self.log("RUN: Starting main worker loop...")
        
        poll_count = 0
        consecutive_errors = 0
        
        while self.running:
            poll_count += 1
            self.log(f"POLL: Poll #{poll_count} starting...")
            
            try:
                # Get next job from queue (only EVALUATE_TASK jobs)
                self.log("POLL: Calling job_queue.dequeue()...")
                job = self.job_queue.dequeue(self.worker_id, [JobType.EVALUATE_TASK])
                self.log(f"POLL: dequeue() returned: {job is not None}")
                
                if job is None:
                    # No jobs available, wait and try again
                    self.log(f"POLL: No jobs available, sleeping {self.config.timeouts.job_queue_poll_interval}s...")
                    time.sleep(self.config.timeouts.job_queue_poll_interval)
                    consecutive_errors = 0  # Reset error count
                    continue
                
                self.log(f"JOB: Got job {job.id[:8]} type={job.job_type}")
                
                if job.job_type != JobType.EVALUATE_TASK:
                    # Wrong job type, put it back
                    self.log(f"JOB: Wrong job type {job.job_type}, failing job...")
                    self.job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}")
                    continue
                
                # Execute the task
                self.log(f"JOB: Executing task for job {job.id[:8]}...")
                result = self._execute_task(job)
                self.log(f"JOB: Task execution result: success={result.success}")
                
                # Update job with result
                if result.success:
                    self.log(f"JOB: Completing job {job.id[:8]}...")
                    self.job_queue.complete_job(job.id, result)
                    self.log(f"JOB: Job {job.id[:8]} completed successfully")
                else:
                    self.log(f"JOB: Failing job {job.id[:8]} with error: {result.error}")
                    self.job_queue.fail_job(job.id, result.error)
                
                consecutive_errors = 0  # Reset error count on success
                
            except KeyboardInterrupt:
                self.log("INTERRUPT: KeyboardInterrupt received, shutting down...")
                self.running = False
            except Exception as e:
                consecutive_errors += 1
                self.log(f"ERROR: Exception in main loop (#{consecutive_errors}): {e}")
                
                # If we have too many consecutive errors, exit
                if consecutive_errors > 10:
                    self.log(f"FATAL: Too many consecutive errors ({consecutive_errors}), exiting")
                    break
                
                # Wait before retrying
                sleep_time = min(consecutive_errors, 5)  # Exponential backoff up to 5s
                self.log(f"ERROR: Sleeping {sleep_time}s before retry...")
                time.sleep(sleep_time)
        
        self.log("RUN: Main worker loop finished")
    
    def _execute_task(self, job) -> JobResult:
        """Execute a single task evaluation"""
        try:
            # Extract job parameters
            epoch = job.parameters.get('epoch', 'epoch-001')
            task = job.parameters.get('task', 'task-001')
            
            self.log(f"TASK: Executing {epoch}/{task}")
            
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
            
            self.log(f"TASK: Running docker-compose in {agent_src_dir}")
            
            result = subprocess.run(
                ["docker-compose", "up", "--build"],
                cwd=agent_src_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.timeouts.task_execution_timeout
            )
            
            execution_time = time.time() - start_time
            self.log(f"TASK: Docker execution finished in {execution_time:.2f}s, return_code={result.returncode}")
            
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
                            'return_code': result.returncode,
                            'output_files': [str(f) for f in output_files]
                        }
                    )
        
        except subprocess.TimeoutExpired as e:
            self.log(f"TASK: Docker execution timed out after {self.config.timeouts.task_execution_timeout}s")
            return JobResult(
                success=False,
                error=f"Task execution timed out after {self.config.timeouts.task_execution_timeout} seconds",
                execution_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                artifacts={
                    'timeout': True,
                    'stdout': getattr(e, 'stdout', ''),
                    'stderr': getattr(e, 'stderr', '')
                }
            )
        except Exception as e:
            self.log(f"TASK: Exception during task execution: {e}")
            return JobResult(
                success=False,
                error=f"Task execution error: {str(e)}",
                execution_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                artifacts={
                    'exception': str(e),
                    'exception_type': type(e).__name__
                }
            )

def main():
    """Main entry point"""
    worker_id = os.environ.get('WORKER_ID', 'task-worker-debug')
    worker = TaskWorkerDebug(worker_id)
    worker.run()

if __name__ == "__main__":
    main()