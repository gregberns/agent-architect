## Essential System Operation Commands

### Start/Stop System
```bash
cd src/agent-eval/orchestrator
python3 orchestrator.py --start    # Start job processing system
python3 orchestrator.py --status   # Check system status
python3 orchestrator.py --stop     # Stop system gracefully
```

### Run Evaluations
```bash
python3 evaluate_epoch.py --epoch epoch-001 --parallel    # Full evaluation
python3 orchestrator.py --retry-failed                    # Retry failed jobs
```

### Generate Reports
```bash
cd ../evaluation/metrics-collectors
python3 metrics_cli.py score --epoch epoch-001      # Score summary
python3 metrics_cli.py report --epoch epoch-001     # Detailed reports
```

### Job Queue Management
```bash
python3 orchestrator.py --status           # Check queue status
python3 orchestrator.py --retry-failed     # Retry failed jobs
python3 orchestrator.py --reset-queue      # Reset stuck jobs
```

### Testing System
```bash
# Run existing tests
python3 test_job_queue.py
python3 test_orchestrator.py
python3 test_evaluate_epoch.py
```