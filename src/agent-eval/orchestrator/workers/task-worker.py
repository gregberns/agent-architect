#!/usr/bin/env python3
"""
Task worker - executes individual task evaluations
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

class TaskWorker:
    """Worker for executing individual task evaluations"""
    
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
        print(f"Task worker {self.worker_id} started")
        
        while self.running:
            try:
                # Get next job from queue
                job = self.job_queue.dequeue(self.worker_id)
                
                if job is None:
                    # No jobs available, wait and try again
                    time.sleep(self.config.timeouts.job_queue_poll_interval)
                    continue
                
                if job.job_type != JobType.EVALUATE_TASK:
                    # Wrong job type, put it back
                    self.job_queue.fail_job(job.id, f"Wrong job type for task worker: {job.job_type}")
                    continue
                
                print(f"Worker {self.worker_id} processing job {job.id[:8]}...")
                
                # Execute the task
                result = self._execute_task(job)
                
                # Update job with result
                if result.success:
                    self.job_queue.complete_job(job.id, result)
                    print(f"Worker {self.worker_id} completed job {job.id[:8]} successfully")
                else:
                    self.job_queue.fail_job(job.id, result.error)
                    print(f"Worker {self.worker_id} failed job {job.id[:8]}: {result.error}")
                
            except KeyboardInterrupt:
                print(f"Worker {self.worker_id} shutting down...")
                self.running = False
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _execute_task(self, job) -> JobResult:
        """Execute a single task evaluation"""
        try:
            # Extract job parameters
            epoch = job.parameters.get('epoch', 'epoch-001')
            task = job.parameters.get('task', 'task-001')
            
            print(f"  Executing {epoch}/{task}")
            
            # Build paths
            base_dir = Path(__file__).parent.parent.parent
            epoch_dir = base_dir / "epochs" / epoch
            agent_src_dir = epoch_dir / "agent-src"
            
            if not agent_src_dir.exists():
                return JobResult(
                    success=False,
                    error=f"Agent source directory not found: {agent_src_dir}"
                )
            
            # Execute docker-compose with unique project name to avoid conflicts
            start_time = time.time()
            
            env = os.environ.copy()
            env['TASK_ID'] = task
            
            # Use unique project name to avoid container name conflicts
            project_name = f"agent-eval-{epoch}-{task}-{int(time.time())}"
            
            result = subprocess.run(
                ["docker-compose", "-p", project_name, "up", "--build"],
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