#!/usr/bin/env python3
"""
Diagnostic worker to debug why orchestrator workers get stuck
"""

import os
import sys
import time
import signal
from pathlib import Path

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobResult
from config_simple import load_config

class DiagnosticWorker:
    """Worker that provides detailed diagnostics"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.running = True
        self.setup_signal_handlers()
        
        print(f"DIAG: Worker {worker_id} starting diagnostics...")
        print(f"DIAG: PID: {os.getpid()}")
        print(f"DIAG: Current directory: {os.getcwd()}")
        print(f"DIAG: Environment variables:")
        for key in ['WORKER_ID', 'WORKER_TYPE']:
            print(f"DIAG:   {key}={os.environ.get(key, 'NOT_SET')}")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"DIAG: Worker {self.worker_id} received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def run(self):
        """Main diagnostic loop"""
        print(f"DIAG: Worker {self.worker_id} starting main loop")
        
        try:
            config = load_config()
            print(f"DIAG: Config loaded successfully")
            print(f"DIAG: Queue file: {config.job_queue_file}")
            print(f"DIAG: Poll interval: {config.timeouts.job_queue_poll_interval}")
            
            job_queue = JobQueue(config.job_queue_file)
            print(f"DIAG: Job queue initialized successfully")
            
            # Get initial stats
            stats = job_queue.get_queue_stats()
            print(f"DIAG: Initial queue stats: {stats}")
            
        except Exception as e:
            print(f"DIAG: ERROR in initialization: {e}")
            import traceback
            traceback.print_exc()
            return
        
        poll_count = 0
        last_stats = None
        
        while self.running and poll_count < 20:  # Limit for testing
            poll_count += 1
            
            try:
                print(f"DIAG: Poll {poll_count} - checking for jobs...")
                
                # Reload queue state to get fresh data
                job_queue.reload_from_file()
                
                # Get current stats and show if changed
                current_stats = job_queue.get_queue_stats()
                if current_stats != last_stats:
                    print(f"DIAG: Queue stats changed: {current_stats}")
                    last_stats = current_stats.copy()
                
                # Try to dequeue a job
                job = job_queue.dequeue(self.worker_id)
                
                if job is None:
                    print(f"DIAG: No jobs available, sleeping {config.timeouts.job_queue_poll_interval}s...")
                    time.sleep(config.timeouts.job_queue_poll_interval)
                    continue
                
                print(f"DIAG: SUCCESSFULLY dequeued job {job.id[:8]}")
                print(f"DIAG: Job type: {job.job_type}")
                print(f"DIAG: Job parameters: {job.parameters}")
                
                # Complete the job quickly without actually running it
                result = JobResult(
                    success=True,
                    output="Diagnostic worker completed job",
                    execution_time=0.5,
                    artifacts={"diagnostic": True, "worker": self.worker_id}
                )
                
                job_queue.complete_job(job.id, result)
                print(f"DIAG: Completed job {job.id[:8]} successfully")
                
                # Continue to process more jobs
                
            except Exception as e:
                print(f"DIAG: ERROR in poll loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
        
        print(f"DIAG: Worker {self.worker_id} finished after {poll_count} polls")

def main():
    """Main entry point"""
    worker_id = os.environ.get('WORKER_ID', 'diagnostic-worker-direct')
    worker = DiagnosticWorker(worker_id)
    worker.run()

if __name__ == "__main__":
    main()