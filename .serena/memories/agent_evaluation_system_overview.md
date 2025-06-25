## Agent Evaluation and Evolution System

### Purpose
Iterative agent development system with two primary phases:
1. **Epoch Evaluation**: Test agent capabilities against standardized programming tasks
2. **Epoch Evolution**: Create improved agent versions through self-modification

### Key Architecture Components
- **Job Queue System**: Manages evaluation tasks with persistence (orchestrator/)
- **Epoch-Based Agent Code**: Versioned agent implementations (epochs/)
- **Standardized Task System**: Template programming tasks (default-workspaces/)
- **Worker Processes**: Execute tasks, validation, and evolution
- **Metrics Collection**: Aggregates results into performance reports

### Current Status
- Phase 1 (Foundation Setup): ✅ Completed - Steps 1-5 done
- Phase 2 (Core Evaluation): 🔄 Step 10 needs revision due to queue system issues
- Job queue system has problems identified in debug_* and test_* files
- Need robust testing framework to ensure system reliability

### Directory Structure
```
src/agent-eval/
├── orchestrator/          # Job queue and management scripts
├── epochs/               # Agent versions (epoch-001, epoch-002...)
├── default-workspaces/   # Template tasks (task-001 to task-005)
└── evaluation/          # Metrics and analysis tools
```

### Critical Issues to Address
- evaluate_epoch.py doesn't automatically trigger validation jobs
- metrics_cli shows "No evaluation job found" - system disconnects
- Queue system reliability problems requiring comprehensive testing