"""
Simple configuration management without external dependencies.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

@dataclass
class ParallelismConfig:
    max_concurrent_jobs: int = 5

@dataclass
class RateLimitingConfig:
    # This is now informational, as rate limiting is not handled by the orchestrator
    api_requests_per_minute: int = 60
    retry_backoff_seconds: List[int] = field(default_factory=lambda: [1, 2, 4, 8, 16])

@dataclass
class RuntimePathsConfig:
    runtime_dir: str = "runtime"
    logs_dir: str = "logs"
    state_dir: str = "state"

    def get_absolute_paths(self, base_dir: Path) -> Dict[str, Path]:
        runtime_base = base_dir / self.runtime_dir
        return {
            "runtime": runtime_base,
            "logs": runtime_base / self.logs_dir,
            "state": runtime_base / self.state_dir,
        }

@dataclass
class TimeoutConfig:
    task_execution_timeout: int = 300  # 5 minutes
    validation_timeout: int = 120      # 2 minutes
    evolution_timeout: int = 1800      # 30 minutes

@dataclass
class OrchestratorConfig:
    parallelism: ParallelismConfig
    rate_limiting: RateLimitingConfig
    runtime_paths: RuntimePathsConfig
    timeouts: TimeoutConfig
    
    @classmethod
    def from_json(cls, json_path: str) -> 'OrchestratorConfig':
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            parallelism=ParallelismConfig(**data.get('parallelism', {})),
            rate_limiting=RateLimitingConfig(**data.get('rate_limiting', {})),
            runtime_paths=RuntimePathsConfig(**data.get('runtime_paths', {})),
            timeouts=TimeoutConfig(**data.get('timeouts', {}))
        )

    @classmethod
    def default(cls) -> 'OrchestratorConfig':
        return cls(
            parallelism=ParallelismConfig(),
            rate_limiting=RateLimitingConfig(),
            runtime_paths=RuntimePathsConfig(),
            timeouts=TimeoutConfig()
        )

    def save_json(self, json_path: str):
        with open(json_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_runtime_paths(self, base_dir: Path = None) -> Dict[str, Path]:
        if base_dir is None:
            base_dir = Path.cwd()
        return self.runtime_paths.get_absolute_paths(base_dir)

def load_config(config_path: str = None) -> OrchestratorConfig:
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            return OrchestratorConfig.from_json(config_path)

    # Default config path
    default_path = Path(__file__).parent / "config.json"
    if default_path.exists():
        return OrchestratorConfig.from_json(str(default_path))
    
    # If no config exists, create a default one
    print("Configuration file not found, creating default config.json")
    config = OrchestratorConfig.default()
    config.save_json(str(default_path))
    return config
