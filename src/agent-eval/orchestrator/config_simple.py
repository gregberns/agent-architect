"""
Simple configuration management without external dependencies.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class ParallelismConfig:
    max_concurrent_jobs: int = 5
    task_evaluation_workers: int = 3
    evolution_workers: int = 2
    validation_workers: int = 2

@dataclass
class RateLimitingConfig:
    api_requests_per_minute: int = 20
    retry_backoff_seconds: List[int] = None
    max_retries: int = 5
    
    def __post_init__(self):
        if self.retry_backoff_seconds is None:
            self.retry_backoff_seconds = [1, 2, 4, 8, 16]

@dataclass
class RuntimePathsConfig:
    runtime_dir: str = "runtime"
    logs_dir: str = "runtime/logs"
    state_dir: str = "runtime/state"
    temp_dir: str = "runtime/temp"
    
    def get_absolute_paths(self, base_dir: Path) -> Dict[str, Path]:
        """Get absolute paths based on base directory"""
        return {
            'runtime': base_dir / self.runtime_dir,
            'logs': base_dir / self.logs_dir,
            'state': base_dir / self.state_dir,
            'temp': base_dir / self.temp_dir
        }

@dataclass
class TimeoutConfig:
    task_execution_timeout: int = 300  # 5 minutes
    evolution_timeout: int = 1800      # 30 minutes
    validation_timeout: int = 120      # 2 minutes
    job_queue_poll_interval: int = 5   # 5 seconds

@dataclass
class OrchestratorConfig:
    parallelism: ParallelismConfig
    rate_limiting: RateLimitingConfig
    timeouts: TimeoutConfig
    runtime_paths: RuntimePathsConfig
    job_queue_file: str = "job_queue.json"  # Will be relative to state_dir
    log_level: str = "INFO"
    
    @classmethod
    def from_json(cls, json_path: str) -> 'OrchestratorConfig':
        """Load configuration from JSON file"""
        json_file = Path(json_path)
        if not json_file.exists():
            # Create default config file
            default_config = cls.default()
            default_config.save_json(json_path)
            return default_config
            
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        return cls(
            parallelism=ParallelismConfig(**data.get('parallelism', {})),
            rate_limiting=RateLimitingConfig(**data.get('rate_limiting', {})),
            timeouts=TimeoutConfig(**data.get('timeouts', {})),
            runtime_paths=RuntimePathsConfig(**data.get('runtime_paths', {})),
            job_queue_file=data.get('job_queue_file', 'job_queue.json'),
            log_level=data.get('log_level', 'INFO')
        )
    
    @classmethod
    def default(cls) -> 'OrchestratorConfig':
        """Create default configuration"""
        return cls(
            parallelism=ParallelismConfig(),
            rate_limiting=RateLimitingConfig(),
            timeouts=TimeoutConfig(),
            runtime_paths=RuntimePathsConfig()
        )
    
    def save_json(self, json_path: str):
        """Save configuration to JSON file"""
        config_dict = asdict(self)
        with open(json_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_runtime_paths(self, base_dir: Path = None) -> Dict[str, Path]:
        """Get runtime paths relative to base directory"""
        if base_dir is None:
            # Default to parent of orchestrator directory (agent-eval root)
            base_dir = Path(__file__).parent.parent
        return self.runtime_paths.get_absolute_paths(base_dir)

def load_config(config_path: str = None) -> OrchestratorConfig:
    """Load configuration from file or create default"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    return OrchestratorConfig.from_json(config_path)