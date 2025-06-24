"""
Configuration management for the agent evaluation orchestrator.
"""

import os
import yaml
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
    job_queue_file: str = "job_queue.json"
    log_level: str = "INFO"
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'OrchestratorConfig':
        """Load configuration from YAML file"""
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            # Create default config file
            default_config = cls.default()
            default_config.save_yaml(yaml_path)
            return default_config
            
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            parallelism=ParallelismConfig(**data.get('parallelism', {})),
            rate_limiting=RateLimitingConfig(**data.get('rate_limiting', {})),
            timeouts=TimeoutConfig(**data.get('timeouts', {})),
            job_queue_file=data.get('job_queue_file', 'job_queue.json'),
            log_level=data.get('log_level', 'INFO')
        )
    
    @classmethod
    def default(cls) -> 'OrchestratorConfig':
        """Create default configuration"""
        return cls(
            parallelism=ParallelismConfig(),
            rate_limiting=RateLimitingConfig(),
            timeouts=TimeoutConfig()
        )
    
    def save_yaml(self, yaml_path: str):
        """Save configuration to YAML file"""
        config_dict = asdict(self)
        with open(yaml_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

def load_config(config_path: str = None) -> OrchestratorConfig:
    """Load configuration from file or create default"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    return OrchestratorConfig.from_yaml(config_path)