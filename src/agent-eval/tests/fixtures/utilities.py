#!/usr/bin/env python3
"""
Test utilities and fixtures for the agent evaluation system
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass
from contextlib import contextmanager

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from job_queue import JobQueue, JobType, JobStatus, Job, JobResult
from config_simple import load_config, OrchestratorConfig


@dataclass
class TestEnvironment:
    """Represents an isolated test environment"""
    temp_dir: Path
    orchestrator_dir: Path
    epochs_dir: Path
    default_workspaces_dir: Path
    queue_file: Path
    config_file: Path
    config: OrchestratorConfig


class TestResults(NamedTuple):
    """Test execution results"""
    passed: int
    failed: int
    errors: List[str]
    execution_time: float


@contextmanager
def test_environment():
    """Create and cleanup test environment"""
    temp_dir = Path(tempfile.mkdtemp(prefix="agent_eval_test_"))
    
    try:
        # Create directory structure
        orchestrator_dir = temp_dir / "orchestrator"
        epochs_dir = temp_dir / "epochs"
        default_workspaces_dir = temp_dir / "default-workspaces"
        
        for dir_path in [orchestrator_dir, epochs_dir, default_workspaces_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create test configuration
        config_file = orchestrator_dir / "config.json"
        queue_file = orchestrator_dir / "job_queue.json"
        
        test_config = {
            "parallelism": {
                "max_concurrent_jobs": 2,
                "task_evaluation_workers": 1,
                "validation_workers": 1,
                "evolution_workers": 1
            },
            "rate_limiting": {
                "api_requests_per_minute": 60,
                "retry_backoff_seconds": 1
            },
            "timeouts": {
                "task_execution_timeout": 30,
                "validation_timeout": 15,
                "evolution_timeout": 60,
                "job_queue_poll_interval": 1
            },
            "files": {
                "job_queue_file": str(queue_file)
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Create empty job queue
        with open(queue_file, 'w') as f:
            json.dump({"jobs": {}, "saved_at": "2025-06-24T00:00:00.000000"}, f)
        
        # Load configuration
        os.environ['AGENT_EVAL_CONFIG'] = str(config_file)
        config = load_config()
        
        env = TestEnvironment(
            temp_dir=temp_dir,
            orchestrator_dir=orchestrator_dir,
            epochs_dir=epochs_dir,
            default_workspaces_dir=default_workspaces_dir,
            queue_file=queue_file,
            config_file=config_file,
            config=config
        )
        
        yield env
        
    finally:
        # Cleanup
        if 'AGENT_EVAL_CONFIG' in os.environ:
            del os.environ['AGENT_EVAL_CONFIG']
        
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def create_test_epoch(env: TestEnvironment, epoch_name: str = "test-epoch-001") -> Path:
    """Create a minimal test epoch with agent-src"""
    epoch_dir = env.epochs_dir / epoch_name
    agent_src_dir = epoch_dir / "agent-src"
    
    # Create directory structure
    for subdir in ["runs", "metrics", "compilation-check", "evolution-workspace"]:
        (epoch_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    agent_src_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal Dockerfile
    dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent.py"]
"""
    (agent_src_dir / "Dockerfile").write_text(dockerfile_content)
    
    # Create minimal requirements.txt
    requirements_content = """requests==2.31.0
"""
    (agent_src_dir / "requirements.txt").write_text(requirements_content)
    
    # Create minimal agent.py
    agent_content = """#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def main():
    task_id = os.environ.get('TASK_ID', 'unknown')
    print(f"Test agent processing task: {task_id}")
    
    # Create simple output
    output_dir = Path("/workspace/output")
    output_dir.mkdir(exist_ok=True)
    
    (output_dir / "solution.py").write_text('''
def hello():
    return "Hello from test agent"

if __name__ == "__main__":
    print(hello())
''')
    
    print("Test agent completed successfully")

if __name__ == "__main__":
    main()
"""
    (agent_src_dir / "agent.py").write_text(agent_content)
    
    # Create docker-compose.yml
    compose_content = f"""version: '3.8'
services:
  agent:
    build: .
    environment:
      - TASK_ID=${{TASK_ID}}
    volumes:
      - ../runs/${{TASK_ID}}:/workspace
    working_dir: /workspace
"""
    (agent_src_dir / "docker-compose.yml").write_text(compose_content)
    
    return epoch_dir


def create_test_task(env: TestEnvironment, task_name: str = "test-task-001") -> Path:
    """Create a test task with input/expected-output"""
    task_dir = env.default_workspaces_dir / task_name
    
    # Create directory structure
    for subdir in ["input", "expected-output", "tests"]:
        (task_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create task description
    task_md_content = f"""# {task_name.title().replace('-', ' ')}

## Objective
Create a simple "Hello World" function for testing purposes.

## Requirements
- Implement a function called `hello()` that returns "Hello World"
- The function should be in a file called `solution.py`

## Example
```python
def hello():
    return "Hello World"
```
"""
    (task_dir / "input" / "TASK.md").write_text(task_md_content)
    
    # Create expected output
    expected_content = """def hello():
    return "Hello World"

if __name__ == "__main__":
    print(hello())
"""
    (task_dir / "expected-output" / "solution.py").write_text(expected_content)
    
    # Create test file
    test_content = """import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'output'))

import pytest
from solution import hello

def test_hello_function():
    result = hello()
    assert result == "Hello World"

def test_hello_return_type():
    result = hello()
    assert isinstance(result, str)
"""
    (task_dir / "tests" / "test_solution.py").write_text(test_content)
    
    return task_dir


def create_test_jobs(job_queue: JobQueue, num_jobs: int = 3) -> List[str]:
    """Create test jobs in the queue"""
    job_ids = []
    
    for i in range(1, num_jobs + 1):
        job_id = job_queue.enqueue(
            JobType.EVALUATE_TASK,
            {
                'epoch': 'test-epoch-001',
                'task': f'test-task-{i:03d}',
                'test_run': True
            },
            max_retries=2
        )
        job_ids.append(job_id)
    
    return job_ids


def simulate_job_completion(job_queue: JobQueue, job_id: str, success: bool = True) -> None:
    """Simulate job completion for testing"""
    if success:
        result = JobResult(
            success=True,
            output="Test job completed successfully",
            execution_time=1.0,
            artifacts={"test": True}
        )
        job_queue.complete_job(job_id, result)
    else:
        job_queue.fail_job(job_id, "Test job failed")


def create_corrupted_queue_file(queue_file: Path, corruption_type: str = "invalid_json") -> None:
    """Create a corrupted queue file for testing recovery"""
    if corruption_type == "invalid_json":
        queue_file.write_text('{"jobs": {invalid json}')
    elif corruption_type == "empty_file":
        queue_file.write_text('')
    elif corruption_type == "missing_jobs_key":
        queue_file.write_text('{"saved_at": "2025-06-24T00:00:00.000000"}')
    elif corruption_type == "truncated":
        valid_content = '{"jobs": {"test": {"id": "test"'
        queue_file.write_text(valid_content)
    else:
        raise ValueError(f"Unknown corruption type: {corruption_type}")


class MockDockerRunner:
    """Mock Docker execution for testing without containers"""
    
    def __init__(self):
        self.calls = []
        self.should_fail = False
        self.should_timeout = False
        self.output_files = []
    
    def simulate_success(self, output_files: List[str]):
        """Configure mock to simulate successful execution"""
        self.should_fail = False
        self.should_timeout = False
        self.output_files = output_files
    
    def simulate_failure(self, error_type: str = "build_error"):
        """Configure mock to simulate execution failure"""
        self.should_fail = True
        self.should_timeout = False
        self.error_type = error_type
    
    def simulate_timeout(self):
        """Configure mock to simulate timeout"""
        self.should_fail = False
        self.should_timeout = True
    
    def run_docker_compose(self, cwd: Path, env: dict, timeout: int) -> tuple:
        """Mock docker-compose execution"""
        self.calls.append({
            'cwd': str(cwd),
            'env': env,
            'timeout': timeout
        })
        
        if self.should_timeout:
            raise TimeoutError("Docker execution timed out")
        
        if self.should_fail:
            return False, f"Docker execution failed: {getattr(self, 'error_type', 'unknown')}"
        
        # Simulate successful execution by creating output files
        if 'TASK_ID' in env:
            task_id = env['TASK_ID']
            output_dir = cwd.parent / "runs" / task_id / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for filename in self.output_files:
                (output_dir / filename).write_text("# Mock generated file")
        
        return True, "Docker execution completed successfully"


def assert_job_state(job_queue: JobQueue, job_id: str, expected_status: JobStatus):
    """Assert that a job has the expected status"""
    job = job_queue.get_job(job_id)
    assert job is not None, f"Job {job_id} not found"
    assert job.status == expected_status, f"Job {job_id} status is {job.status}, expected {expected_status}"


def wait_for_job_completion(job_queue: JobQueue, job_ids: List[str], timeout: int = 30) -> bool:
    """Wait for jobs to complete, return True if all completed"""
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job_queue.reload_from_file()
        
        all_completed = True
        for job_id in job_ids:
            job = job_queue.get_job(job_id)
            if not job or job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                all_completed = False
                break
        
        if all_completed:
            return True
        
        time.sleep(1)
    
    return False


def print_test_summary(results: TestResults):
    """Print a formatted test summary"""
    total = results.passed + results.failed
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total tests: {total}")
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Success rate: {(results.passed/total*100 if total > 0 else 0):.1f}%")
    print(f"Execution time: {results.execution_time:.2f}s")
    
    if results.errors:
        print(f"\nErrors ({len(results.errors)}):")
        for i, error in enumerate(results.errors, 1):
            print(f"  {i}. {error}")
    
    print(f"{'='*50}")


if __name__ == "__main__":
    print("Testing utilities module")
    
    # Test the test environment creation
    with test_environment() as env:
        print(f"✅ Created test environment at: {env.temp_dir}")
        
        # Test epoch creation
        epoch_dir = create_test_epoch(env)
        print(f"✅ Created test epoch at: {epoch_dir}")
        
        # Test task creation
        task_dir = create_test_task(env)
        print(f"✅ Created test task at: {task_dir}")
        
        # Test job queue operations
        job_queue = JobQueue(env.queue_file)
        job_ids = create_test_jobs(job_queue, 2)
        print(f"✅ Created {len(job_ids)} test jobs")
        
        # Test job completion simulation
        simulate_job_completion(job_queue, job_ids[0], success=True)
        assert_job_state(job_queue, job_ids[0], JobStatus.COMPLETED)
        print(f"✅ Simulated job completion")
        
    print("✅ All utility tests passed!")