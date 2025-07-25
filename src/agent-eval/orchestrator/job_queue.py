"""
Job queue implementation for agent evaluation orchestrator.
"""

import json
import uuid
import time
import threading
import fcntl
import os
import tempfile
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    EVALUATE_TASK = "evaluate_task"
    EVOLVE_EPOCH = "evolve_epoch"
    COMPILE_CHECK = "compile_check"
    GENERATE_METRICS = "generate_metrics"

@dataclass
class JobResult:
    success: bool
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    artifacts: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}

@dataclass
class Job:
    id: str
    job_type: JobType
    status: JobStatus
    parameters: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[JobResult] = None
    retry_count: int = 0
    max_retries: int = 3
    worker_id: Optional[str] = None
    
    @classmethod
    def create(cls, job_type: Union[JobType, str], parameters: Dict[str, Any], 
               max_retries: int = 3) -> 'Job':
        """Create a new job"""
        if isinstance(job_type, str):
            job_type = JobType(job_type)
            
        return cls(
            id=str(uuid.uuid4()),
            job_type=job_type,
            status=JobStatus.PENDING,
            parameters=parameters,
            created_at=datetime.now(),
            max_retries=max_retries
        )
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries
    
    def mark_running(self, worker_id: str):
        """Mark job as running"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
        self.worker_id = worker_id
    
    def mark_completed(self, result: JobResult):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
    
    def mark_failed(self, error: str, allow_retry: bool = True):
        """Mark job as failed"""
        if allow_retry and self.can_retry():
            self.retry_count += 1
            self.status = JobStatus.PENDING
            self.started_at = None
            self.worker_id = None
        else:
            self.status = JobStatus.FAILED
            self.completed_at = datetime.now()
            
        if self.result is None:
            self.result = JobResult(success=False, error=error)
        else:
            self.result.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field] is not None:
                data[field] = data[field].isoformat()
        # Convert enums to strings
        data['job_type'] = self.job_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        # Convert datetime strings back to datetime objects
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field] is not None:
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert string enums back to enum objects
        data['job_type'] = JobType(data['job_type'])
        data['status'] = JobStatus(data['status'])
        
        # Handle result field
        if data.get('result') is not None:
            data['result'] = JobResult(**data['result'])
        
        return cls(**data)

class JobQueue:
    def __init__(self, persistence_file: str = "job_queue.json", silent: bool = False):
        # Handle both absolute and relative paths
        if Path(persistence_file).is_absolute():
            self.persistence_file = Path(persistence_file)
        else:
            self.persistence_file = Path(persistence_file)
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.RLock()
        self.silent = silent  # Suppress error messages when True
        self.load_from_file()
    
    def enqueue(self, job_type: Union[JobType, str], parameters: Dict[str, Any], 
                max_retries: int = 3) -> str:
        """Add a job to the queue"""
        job = Job.create(job_type, parameters, max_retries)
        
        with self._lock:
            self.jobs[job.id] = job
            self.save_to_file()
        
        return job.id
    
    def dequeue(self, worker_id: str, job_types: List[JobType] = None) -> Optional[Job]:
        """Get the next pending job and mark it as running"""
        with self._lock:
            # Always reload from file to see fresh jobs from other processes
            self.load_from_file()
            
            for job in self.jobs.values():
                if job.status == JobStatus.PENDING:
                    # If job_types specified, only return matching job types
                    if job_types and job.job_type not in job_types:
                        continue
                    job.mark_running(worker_id)
                    self.save_to_file()
                    return job
        return None
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a specific job by ID"""
        with self._lock:
            return self.jobs.get(job_id)
    
    def complete_job(self, job_id: str, result: JobResult):
        """Mark a job as completed"""
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].mark_completed(result)
                self.save_to_file()
    
    def fail_job(self, job_id: str, error: str, allow_retry: bool = True):
        """Mark a job as failed"""
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].mark_failed(error, allow_retry)
                self.save_to_file()
    
    def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status"""
        with self._lock:
            return [job for job in self.jobs.values() if job.status == status]
    
    def get_jobs_by_type(self, job_type: JobType) -> List[Job]:
        """Get all jobs of a specific type"""
        with self._lock:
            return [job for job in self.jobs.values() if job.job_type == job_type]
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        with self._lock:
            return list(self.jobs.values())
    
    def clear_completed_jobs(self, older_than: timedelta = None):
        """Remove completed jobs older than the specified time"""
        if older_than is None:
            older_than = timedelta(hours=24)  # Default: 24 hours
        
        cutoff_time = datetime.now() - older_than
        
        with self._lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED] and 
                    job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
            
            if jobs_to_remove:
                self.save_to_file()
            
            return len(jobs_to_remove)
    
    def retry_failed_jobs(self) -> int:
        """Retry all retryable failed jobs"""
        with self._lock:
            retried_count = 0
            for job in self.jobs.values():
                if job.can_retry():
                    job.status = JobStatus.PENDING
                    job.started_at = None
                    job.worker_id = None
                    retried_count += 1
            
            if retried_count > 0:
                self.save_to_file()
            
            return retried_count
    
    def reset_running_jobs(self) -> int:
        """Reset jobs stuck in RUNNING state to PENDING (for orchestrator restart)"""
        with self._lock:
            reset_count = 0
            for job in self.jobs.values():
                if job.status == JobStatus.RUNNING:
                    job.status = JobStatus.PENDING
                    job.started_at = None
                    job.worker_id = None
                    reset_count += 1
            
            if reset_count > 0:
                self.save_to_file()
            
            return reset_count
    
    def clear_all_jobs(self) -> int:
        """Clear all jobs from the queue (DANGEROUS!)"""
        with self._lock:
            job_count = len(self.jobs)
            self.jobs.clear()
            if job_count > 0:
                self.save_to_file()
            return job_count
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        with self._lock:
            stats = {status.value: 0 for status in JobStatus}
            for job in self.jobs.values():
                stats[job.status.value] += 1
            return stats
    
    def save_to_file(self):
        """Save queue state to file with atomic write"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = {
                    'jobs': {job_id: job.to_dict() for job_id, job in self.jobs.items()},
                    'saved_at': datetime.now().isoformat()
                }
                
                # Use atomic write with temporary file in same directory
                temp_fd, temp_path = tempfile.mkstemp(
                    suffix='.tmp', 
                    prefix='job_queue_', 
                    dir=self.persistence_file.parent
                )
                
                try:
                    with os.fdopen(temp_fd, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                        f.flush()
                        os.fsync(f.fileno())  # Force write to disk
                    
                    # Atomic move
                    os.replace(temp_path, self.persistence_file)
                    return  # Success
                    
                except Exception as e:
                    # Clean up temp file on error
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    raise e
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Error saving job queue after {max_retries} attempts: {e}")
    
    def load_from_file(self):
        """Load queue state from file with robust error handling"""
        if not self.persistence_file.exists():
            return
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Try to read the file
                with open(self.persistence_file, 'r') as f:
                    content = f.read()
                
                # Skip empty files
                if not content.strip():
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    else:
                        self.jobs = {}
                        return
                
                # Parse JSON
                data = json.loads(content)
                jobs_data = data.get('jobs', {})
                
                # Load jobs one by one, skipping corrupted ones
                self.jobs = {}
                for job_id, job_data in jobs_data.items():
                    try:
                        self.jobs[job_id] = Job.from_dict(job_data)
                    except (KeyError, ValueError, TypeError) as job_error:
                        # Skip corrupted job but log the issue
                        if not self.silent:
                            print(f"Warning: Skipping corrupted job {job_id}: {job_error}")
                        continue
                        
                return  # Success
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries - 1:
                    # JSON corruption, wait and retry
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    if not self.silent:
                        print(f"Error loading job queue after {max_retries} attempts: {e}")
                    # Try to recover by clearing corrupted data
                    self.jobs = {}
                    # Save empty state to fix corruption
                    try:
                        self.save_to_file()
                    except:
                        pass
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    print(f"Error loading job queue: {e}")
                    self.jobs = {}
                    return
    
    def reload_from_file(self):
        """Reload queue state from file (for monitoring fresh updates)"""
        with self._lock:
            self.load_from_file()