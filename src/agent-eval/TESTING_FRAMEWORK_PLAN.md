# Agent Evaluation System - Testing Framework Plan

## Overview

This document outlines a comprehensive testing framework to ensure the queue system and overall agent evaluation system works reliably. The framework addresses all issues identified in the debug/test files and provides a robust foundation for future development.

## Testing Philosophy

### 1. Test Categories
- **Unit Tests**: Individual component validation
- **Integration Tests**: Component interaction validation
- **System Tests**: End-to-end workflow validation
- **Stress Tests**: Performance and reliability under load
- **Recovery Tests**: System resilience and error handling

### 2. Test Organization
```
tests/
├── unit/                    # Individual component tests
│   ├── test_job_queue.py
│   ├── test_config.py
│   ├── test_workers.py
│   └── test_metrics.py
├── integration/             # Component interaction tests
│   ├── test_orchestrator_workers.py
│   ├── test_evaluation_pipeline.py
│   └── test_docker_execution.py
├── system/                  # End-to-end tests
│   ├── test_full_evaluation.py
│   ├── test_epoch_lifecycle.py
│   └── test_metrics_generation.py
├── stress/                  # Performance tests
│   ├── test_concurrent_jobs.py
│   ├── test_large_queues.py
│   └── test_resource_limits.py
├── recovery/                # Error handling tests
│   ├── test_queue_corruption.py
│   ├── test_worker_crashes.py
│   └── test_docker_failures.py
└── fixtures/                # Test data and utilities
    ├── test_epochs/
    ├── test_tasks/
    └── utilities.py
```

## Specific Test Requirements

### Unit Tests

#### 1. Job Queue (`test_job_queue.py`)
- **Enqueue/Dequeue Operations**
  - Basic job creation and retrieval
  - Worker assignment and job claiming
  - Queue statistics calculation
  - Job state transitions (PENDING → RUNNING → COMPLETED/FAILED)

- **Persistence**
  - File save/load operations
  - JSON corruption handling
  - Concurrent access safety
  - Backup and recovery

- **Error Handling**
  - Invalid job parameters
  - Worker timeout scenarios
  - File system errors

#### 2. Configuration (`test_config.py`)
- Configuration loading from JSON
- Default value handling
- Configuration validation
- Environment variable overrides

#### 3. Workers (`test_workers.py`)
- Task worker job processing
- Validation worker execution
- Worker error handling
- Docker container management

### Integration Tests

#### 1. Orchestrator-Worker Communication (`test_orchestrator_workers.py`)
- Worker process spawning
- Job distribution to workers
- Worker failure detection and recovery
- Graceful shutdown handling

#### 2. Evaluation Pipeline (`test_evaluation_pipeline.py`)
- evaluate_epoch.py job enqueuing
- Job monitoring and completion detection
- Result collection and aggregation
- Error propagation and handling

#### 3. Docker Execution (`test_docker_execution.py`)
- Container build and execution
- File mounting and workspace setup
- Environment variable passing
- Output collection and validation

### System Tests

#### 1. Full Evaluation (`test_full_evaluation.py`)
- Complete epoch evaluation workflow
- All default tasks processing
- Metrics generation and reporting
- Cross-epoch comparisons

#### 2. Epoch Lifecycle (`test_epoch_lifecycle.py`)
- Epoch creation and setup
- Task copying and execution
- Results validation and storage
- Cleanup and archival

### Stress Tests

#### 1. Concurrent Jobs (`test_concurrent_jobs.py`)
- Multiple workers processing simultaneously
- Queue contention handling
- Resource utilization monitoring
- Performance benchmarking

#### 2. Large Queues (`test_large_queues.py`)
- Processing 100+ jobs
- Memory usage validation
- Queue file size management
- Performance degradation analysis

### Recovery Tests

#### 1. Queue Corruption (`test_queue_corruption.py`)
- JSON corruption detection
- Automatic recovery mechanisms
- Backup restoration
- Data integrity validation

#### 2. Worker Crashes (`test_worker_crashes.py`)
- Worker process termination handling
- Job state recovery
- Automatic restart mechanisms
- Error logging and reporting

#### 3. Docker Failures (`test_docker_failures.py`)
- Container build failures
- Runtime execution errors
- Resource exhaustion handling
- Cleanup after failures

## Test Implementation Strategy

### 1. Test Fixtures and Utilities

#### Test Epoch Setup
```python
# tests/fixtures/utilities.py
def create_test_epoch(epoch_name: str) -> Path:
    """Create a minimal test epoch with agent-src"""
    
def create_test_task(task_name: str) -> Path:
    """Create a test task with input/expected-output"""
    
def setup_test_environment() -> TestEnvironment:
    """Setup isolated test environment with temp directories"""
    
def cleanup_test_environment(env: TestEnvironment):
    """Clean up test resources"""
```

#### Mock Docker Execution
```python
class MockDockerRunner:
    """Mock Docker execution for testing without containers"""
    
    def simulate_success(self, output_files: List[str])
    def simulate_failure(self, error_type: str)
    def simulate_timeout()
```

### 2. Test Execution Framework

#### Test Runner (`run_tests.py`)
```python
#!/usr/bin/env python3
"""
Comprehensive test runner for the agent evaluation system
"""

def run_unit_tests() -> TestResults
def run_integration_tests() -> TestResults  
def run_system_tests() -> TestResults
def run_stress_tests() -> TestResults
def run_recovery_tests() -> TestResults

def run_all_tests() -> TestResults
def run_critical_tests() -> TestResults  # Fast subset for CI
def run_pre_commit_tests() -> TestResults  # Quick validation

def generate_test_report(results: TestResults)
```

#### Continuous Testing (`watch_tests.py`)
```python
#!/usr/bin/env python3
"""
File watcher that runs relevant tests when code changes
"""

def watch_for_changes()
def run_relevant_tests(changed_files: List[str])
```

### 3. Test Configuration

#### Test Configuration (`tests/test_config.json`)
```json
{
  "test_timeouts": {
    "unit_test_timeout": 10,
    "integration_test_timeout": 60,
    "system_test_timeout": 300,
    "stress_test_timeout": 600
  },
  "test_environments": {
    "temp_dir_prefix": "agent_eval_test_",
    "cleanup_on_success": true,
    "preserve_on_failure": true
  },
  "mock_settings": {
    "use_mock_docker": true,
    "simulate_api_delays": false,
    "inject_random_failures": false
  }
}
```

## Test Data and Scenarios

### 1. Test Tasks
- **Minimal Task**: Simple "Hello World" for basic validation
- **Complex Task**: Multi-file solution requiring imports and classes
- **Failing Task**: Intentionally impossible task to test error handling
- **Timeout Task**: Long-running task to test timeout mechanisms

### 2. Test Epochs
- **Valid Epoch**: Complete agent-src with working Docker setup
- **Broken Epoch**: Missing files or invalid Docker configuration
- **Legacy Epoch**: Different agent implementation for compatibility testing

### 3. Queue Scenarios
- **Empty Queue**: No jobs, all workers idle
- **Single Job**: Basic processing scenario
- **Full Queue**: Maximum capacity testing
- **Mixed Jobs**: Different job types and priorities
- **Corrupted Queue**: Various JSON corruption patterns

## Test Automation and CI/CD

### 1. Pre-Commit Hooks
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running pre-commit tests..."
python tests/run_tests.py --pre-commit
if [ $? -ne 0 ]; then
    echo "Tests failed - commit blocked"
    exit 1
fi
```

### 2. Post-Change Validation
```bash
#!/bin/bash
# scripts/validate_changes.sh
echo "Running full test suite..."
python tests/run_tests.py --all
echo "Generating test report..."
python tests/run_tests.py --report
```

### 3. Scheduled Health Checks
```bash
#!/bin/bash
# scripts/system_health_check.sh
# Run critical tests every hour
python tests/run_tests.py --critical
```

## Success Criteria

### 1. Test Coverage
- **Unit Tests**: 95%+ code coverage for core components
- **Integration Tests**: All component interactions validated
- **System Tests**: Complete workflows tested end-to-end
- **Recovery Tests**: All failure modes have recovery paths

### 2. Test Reliability
- **Deterministic**: Tests produce consistent results
- **Isolated**: Tests don't interfere with each other
- **Fast**: Unit tests complete in <30s, integration in <5min
- **Clear**: Test failures provide actionable error messages

### 3. System Reliability
- **Queue Corruption**: Automatic detection and recovery
- **Worker Failures**: Graceful handling and restart
- **Docker Issues**: Clear error reporting and fallback options
- **Performance**: System handles 50+ concurrent jobs reliably

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Setup test framework structure
2. Implement core utilities and fixtures
3. Create basic unit tests for job queue
4. Add integration tests for orchestrator-worker communication

### Phase 2: Core Testing (Week 2)
1. Complete unit test suite
2. Add system tests for full evaluation workflow
3. Implement recovery tests for queue corruption
4. Create test runner and automation

### Phase 3: Advanced Testing (Week 3)
1. Add stress tests for performance validation
2. Implement continuous testing and file watching
3. Create comprehensive error scenario tests
4. Add performance benchmarking and monitoring

### Phase 4: Integration (Week 4)
1. Integrate with existing codebase
2. Update documentation and operations guide
3. Train team on test execution and interpretation
4. Establish testing procedures for future development

## Long-term Maintenance

### 1. Test Evolution
- Add new tests for each bug discovered
- Update tests when system architecture changes
- Regularly review and refactor test code
- Maintain test performance and reliability

### 2. Monitoring and Alerting
- Set up automated test execution schedules
- Create dashboards for test results and system health
- Implement alerting for test failures
- Track test execution time and resource usage

### 3. Documentation
- Keep test documentation up-to-date
- Document test failure troubleshooting procedures
- Maintain test best practices guide
- Record lessons learned and common patterns

This testing framework provides comprehensive coverage of all identified issues and establishes a foundation for reliable system operation moving forward.