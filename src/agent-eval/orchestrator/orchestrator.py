#!/usr/bin/env python3
"""
Main orchestrator for agent evaluation system.
Manages job queue and worker processes.
"""

import os
import sys
import time
import json
import signal
import argparse
import threading
import subprocess
import multiprocessing
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from job_queue import JobQueue, JobType, JobStatus, JobResult
from config_simple import load_config, OrchestratorConfig

class WorkerProcess:
    """Represents a worker process"""
    
    def __init__(self, worker_id: str, worker_type: str, script_path: str):
        self.worker_id = worker_id
        self.worker_type = worker_type
        self.script_path = script_path
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.current_job_id: Optional[str] = None
        self.last_heartbeat: Optional[datetime] = None
    
    def start(self) -> bool:
        """Start the worker process"""
        try:
            # Start worker process with environment variables
            env = os.environ.copy()
            env['WORKER_ID'] = self.worker_id
            env['WORKER_TYPE'] = self.worker_type
            
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                start_new_session=True
            )
            
            self.started_at = datetime.now()
            print(f"Started worker {self.worker_id} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            print(f"Failed to start worker {self.worker_id}: {e}")
            return False
    
    def stop(self, timeout: int = 10) -> bool:
        """Stop the worker process gracefully"""
        if not self.process:
            return True
        
        try:
            # Try graceful shutdown first
            self.process.terminate()
            
            try:
                self.process.wait(timeout=timeout)
                print(f"Worker {self.worker_id} stopped gracefully")
                return True
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                print(f"Worker {self.worker_id} did not stop gracefully, force killing")
                self.process.kill()
                self.process.wait()
                return True
                
        except Exception as e:
            print(f"Error stopping worker {self.worker_id}: {e}")
            return False
    
    def is_alive(self) -> bool:
        """Check if worker process is still alive"""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def get_status(self) -> Dict:
        """Get worker status information"""
        return {
            'worker_id': self.worker_id,
            'worker_type': self.worker_type,
            'is_alive': self.is_alive(),
            'pid': self.process.pid if self.process else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'current_job_id': self.current_job_id,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }

class Orchestrator:
    """Main orchestrator for managing job queue and workers"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.job_queue = JobQueue(self.config.job_queue_file)
        self.workers: Dict[str, WorkerProcess] = {}
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Status persistence
        self.base_dir = Path(__file__).parent
        self.status_file = self.base_dir / "orchestrator_status.json"
        self.pid_file = self.base_dir / "orchestrator.pid"
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the orchestrator and all workers"""
        print("Starting Agent Evaluation Orchestrator...")
        print(f"Configuration: {self.config.parallelism.max_concurrent_jobs} max jobs")
        
        # Reset any jobs stuck in RUNNING state from previous orchestrator crash
        reset_count = self.job_queue.reset_running_jobs()
        if reset_count > 0:
            print(f"Reset {reset_count} jobs stuck in RUNNING state to PENDING")
        
        self.running = True
        
        # Start worker processes
        self._start_workers()
        
        # Save initial status
        self._save_status()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("Orchestrator started successfully")
        print("Press Ctrl+C to stop")
        
        # Main loop
        try:
            while self.running:
                time.sleep(5)  # Save status every 5 seconds
                if self.running:  # Check again in case we're shutting down
                    self._save_status()
        except KeyboardInterrupt:
            print("\\nShutdown requested...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the orchestrator and all workers"""
        print("Stopping orchestrator...")
        self.running = False
        
        # Stop all workers
        self._stop_workers()
        
        # Clean up status files
        self._cleanup_status_files()
        
        print("Orchestrator stopped")
    
    def _start_workers(self):
        """Start worker processes based on configuration"""
        workers_dir = Path(__file__).parent / "workers"
        
        # Task evaluation workers
        for i in range(self.config.parallelism.task_evaluation_workers):
            worker_id = f"task-worker-{i+1}"
            script_path = workers_dir / "task-worker-debug.py"
            
            if script_path.exists():
                worker = WorkerProcess(worker_id, "task_evaluation", str(script_path))
                if worker.start():
                    self.workers[worker_id] = worker
            else:
                print(f"Warning: Worker script not found: {script_path}")
        
        # Evolution workers
        for i in range(self.config.parallelism.evolution_workers):
            worker_id = f"evolution-worker-{i+1}"
            script_path = workers_dir / "evolution-worker.py"
            
            if script_path.exists():
                worker = WorkerProcess(worker_id, "evolution", str(script_path))
                if worker.start():
                    self.workers[worker_id] = worker
            else:
                print(f"Warning: Worker script not found: {script_path}")
        
        # Validation workers
        for i in range(self.config.parallelism.validation_workers):
            worker_id = f"validation-worker-{i+1}"
            script_path = workers_dir / "validation-worker.py"
            
            if script_path.exists():
                worker = WorkerProcess(worker_id, "validation", str(script_path))
                if worker.start():
                    self.workers[worker_id] = worker
            else:
                print(f"Warning: Worker script not found: {script_path}")
        
        print(f"Started {len(self.workers)} workers")
    
    def _stop_workers(self):
        """Stop all worker processes"""
        for worker_id, worker in self.workers.items():
            worker.stop()
        
        self.workers.clear()
    
    def _monitor_loop(self):
        """Monitor workers and restart if needed"""
        while self.running:
            try:
                # Check worker health
                dead_workers = []
                for worker_id, worker in self.workers.items():
                    if not worker.is_alive():
                        print(f"Worker {worker_id} has died, will restart")
                        dead_workers.append(worker_id)
                
                # Restart dead workers
                for worker_id in dead_workers:
                    old_worker = self.workers[worker_id]
                    print(f"Restarting worker {worker_id}")
                    
                    new_worker = WorkerProcess(
                        old_worker.worker_id,
                        old_worker.worker_type,
                        old_worker.script_path
                    )
                    
                    if new_worker.start():
                        self.workers[worker_id] = new_worker
                    else:
                        print(f"Failed to restart worker {worker_id}")
                        del self.workers[worker_id]
                
                # Clean up old completed jobs
                self.job_queue.clear_completed_jobs(timedelta(hours=1))
                
                time.sleep(self.config.timeouts.job_queue_poll_interval)
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(5)
    
    def _save_status(self):
        """Save orchestrator status to file"""
        try:
            status = {
                'running': self.running,
                'pid': os.getpid(),
                'started_at': datetime.now().isoformat(),
                'workers': {
                    worker_id: {
                        'worker_id': worker.worker_id,
                        'worker_type': worker.worker_type,
                        'pid': worker.process.pid if worker.process else None,
                        'started_at': worker.started_at.isoformat() if worker.started_at else None,
                        'is_alive': worker.is_alive()
                    }
                    for worker_id, worker in self.workers.items()
                },
                'config': {
                    'max_concurrent_jobs': self.config.parallelism.max_concurrent_jobs,
                    'task_workers': self.config.parallelism.task_evaluation_workers,
                    'evolution_workers': self.config.parallelism.evolution_workers,
                    'validation_workers': self.config.parallelism.validation_workers
                }
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            # Also write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
                
        except Exception as e:
            print(f"Warning: Could not save status: {e}")
    
    def _load_status(self) -> Optional[Dict]:
        """Load orchestrator status from file"""
        try:
            if not self.status_file.exists():
                return None
            
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            # Check if the process is actually running
            if 'pid' in status:
                try:
                    # Check if process exists (works on Unix-like systems)
                    os.kill(status['pid'], 0)
                    return status
                except (OSError, ProcessLookupError):
                    # Process doesn't exist, remove stale files
                    self._cleanup_status_files()
                    return None
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not load status: {e}")
            return None
    
    def _cleanup_status_files(self):
        """Clean up stale status files"""
        try:
            if self.status_file.exists():
                self.status_file.unlink()
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception as e:
            print(f"Warning: Could not cleanup status files: {e}")
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        # If this instance is not the running orchestrator, try to load status from file
        if not self.running:
            persisted_status = self._load_status()
            if persisted_status:
                # Add current queue stats to persisted status
                persisted_status['queue'] = self.job_queue.get_queue_stats()
                return persisted_status
        
        # Return current instance status
        queue_stats = self.job_queue.get_queue_stats()
        worker_statuses = [worker.get_status() for worker in self.workers.values()]
        
        return {
            'running': self.running,
            'workers': {
                'total': len(self.workers),
                'alive': sum(1 for w in self.workers.values() if w.is_alive()),
                'details': worker_statuses
            },
            'queue': queue_stats,
            'config': {
                'max_concurrent_jobs': self.config.parallelism.max_concurrent_jobs,
                'task_workers': self.config.parallelism.task_evaluation_workers,
                'evolution_workers': self.config.parallelism.evolution_workers,
                'validation_workers': self.config.parallelism.validation_workers
            }
        }
    
    def print_status(self):
        """Print current status to console"""
        status = self.get_status()
        
        print("\\n" + "="*60)
        print("ORCHESTRATOR STATUS")
        print("="*60)
        print(f"Running: {status['running']}")
        
        # Handle both persisted status format and live status format
        if 'workers' in status:
            if isinstance(status['workers'], dict) and 'alive' in status['workers']:
                # Live status format
                print(f"Workers: {status['workers']['alive']}/{status['workers']['total']} alive")
                worker_details = status['workers'].get('details', [])
            else:
                # Persisted status format - workers is a dict of worker_id -> worker_info
                worker_details = list(status['workers'].values())
                alive_count = sum(1 for w in worker_details if w.get('is_alive', False))
                total_count = len(worker_details)
                print(f"Workers: {alive_count}/{total_count} alive")
        else:
            print("Workers: 0/0 alive")
            worker_details = []
        
        print("\\nQueue Status:")
        for status_name, count in status.get('queue', {}).items():
            print(f"  {status_name.title()}: {count}")
        
        print("\\nWorkers:")
        for worker in worker_details:
            alive_status = "✅" if worker.get('is_alive', False) else "❌"
            worker_id = worker.get('worker_id', 'unknown')
            worker_type = worker.get('worker_type', 'unknown')
            pid = worker.get('pid', 'unknown')
            print(f"  {alive_status} {worker_id} ({worker_type}) PID:{pid}")
        
        if status.get('pid'):
            print(f"\\nOrchestrator PID: {status['pid']}")
        
        print("="*60)
    
    def retry_failed_jobs(self) -> int:
        """Retry all failed jobs that can be retried"""
        return self.job_queue.retry_failed_jobs()

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Agent Evaluation Orchestrator")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--start", action="store_true", help="Start the orchestrator")
    parser.add_argument("--status", action="store_true", help="Show orchestrator status")
    parser.add_argument("--stop", action="store_true", help="Stop the orchestrator")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed jobs")
    parser.add_argument("--clear-queue", action="store_true", help="Clear completed jobs")
    parser.add_argument("--reset-queue", action="store_true", help="Reset stuck running jobs to pending")
    parser.add_argument("--clear-all-jobs", action="store_true", help="Clear ALL jobs (DANGEROUS!)")
    
    args = parser.parse_args()
    
    # Create orchestrator instance
    orchestrator = Orchestrator(args.config)
    
    if args.start:
        orchestrator.start()
    
    elif args.status:
        orchestrator.print_status()
    
    elif args.retry_failed:
        retried = orchestrator.retry_failed_jobs()
        print(f"Retried {retried} failed jobs")
    
    elif args.stop:
        # Load status to find running orchestrator
        persisted_status = orchestrator._load_status()
        if persisted_status and persisted_status.get('pid'):
            pid = persisted_status['pid']
            try:
                # Send SIGTERM to running orchestrator
                os.kill(pid, signal.SIGTERM)
                print(f"Sent stop signal to orchestrator (PID: {pid})")
                
                # Wait a moment for graceful shutdown
                time.sleep(2)
                
                # Check if it's still running
                try:
                    os.kill(pid, 0)
                    print(f"Orchestrator still running, sending SIGKILL...")
                    os.kill(pid, signal.SIGKILL)
                except (OSError, ProcessLookupError):
                    pass  # Process already stopped
                
                # Clean up status files
                orchestrator._cleanup_status_files()
                print("Orchestrator stopped")
                
            except (OSError, ProcessLookupError):
                print("Orchestrator process not found (may have already stopped)")
                orchestrator._cleanup_status_files()
        else:
            print("No running orchestrator found")
    
    elif args.clear_queue:
        orchestrator.job_queue.clear_completed_jobs(timedelta(minutes=1))
        print("Cleared completed jobs")
    
    elif args.reset_queue:
        reset_count = orchestrator.job_queue.reset_running_jobs()
        print(f"Reset {reset_count} stuck running jobs to pending")
    
    elif args.clear_all_jobs:
        response = input("This will DELETE ALL JOBS from the queue. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            cleared_count = orchestrator.job_queue.clear_all_jobs()
            print(f"Cleared {cleared_count} jobs from the queue")
        else:
            print("Operation cancelled")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()