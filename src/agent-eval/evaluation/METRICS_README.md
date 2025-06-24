# Metrics Collection System

The metrics collection system provides comprehensive tools for analyzing agent performance across tasks and epochs. It aggregates validation results into meaningful scores and generates detailed reports for performance tracking and evolution guidance.

## Overview

The system consists of three main components:
- **Score Calculator**: Aggregates validation results into task and epoch scores
- **Report Generator**: Creates JSON and CSV reports for performance analysis
- **Epoch Analyzer**: Provides trend analysis and performance pattern detection

## Scoring System

### Task-Level Scoring (2-point system)
- **Compilation Score**: 1 point if all generated Python files compile successfully
- **Test Score**: 1 point if all tests pass
- **Total Score**: 0-2 points per task

### Epoch-Level Scoring
- **Total Score**: Sum of all task scores in the epoch
- **Max Possible Score**: Number of tasks × 2
- **Success Rate**: (Total Score / Max Possible Score) × 100%
- **Compilation Success Rate**: Percentage of tasks that compiled successfully
- **Test Success Rate**: Percentage of tasks that passed tests

## Components

### 1. Score Calculator (`score_calculator.py`)

Calculates scores by examining job queue results and validation artifacts.

**Usage:**
```bash
# Calculate epoch score
python3 score_calculator.py --epoch epoch-001

# Calculate specific task score
python3 score_calculator.py --epoch epoch-001 --task task-001

# Get validation summary for debugging
python3 score_calculator.py --epoch epoch-001 --validation-summary
```

**Key Classes:**
- `TaskScore`: Individual task performance metrics
- `EpochScore`: Aggregated epoch performance metrics  
- `ScoreCalculator`: Main calculation engine

### 2. Report Generator (`report_generator.py`)

Generates comprehensive reports in JSON and CSV formats.

**Usage:**
```bash
# Generate reports for single epoch
python3 report_generator.py --epoch epoch-001

# Generate comparison report across epochs
python3 report_generator.py --compare epoch-001 epoch-002 epoch-003

# List available epochs
python3 report_generator.py --list-epochs

# Custom output directory and formats
python3 report_generator.py --epoch epoch-001 --output-dir ./reports --formats json csv
```

**Report Types:**
- **Single Epoch Reports**: Detailed breakdown of task performance
- **Comparison Reports**: Cross-epoch performance analysis
- **JSON Format**: Machine-readable with full metadata
- **CSV Format**: Human-readable for spreadsheet analysis

### 3. Epoch Analyzer (`epoch_analyzer.py`)

Provides advanced analysis including trend detection and performance patterns.

**Usage:**
```bash
# Analyze trends across epochs
python3 epoch_analyzer.py --epochs epoch-001 epoch-002 epoch-003

# Focus on specific analysis types
python3 epoch_analyzer.py --epochs epoch-001 epoch-002 --trends-only
python3 epoch_analyzer.py --epochs epoch-001 epoch-002 --tasks-only
python3 epoch_analyzer.py --epochs epoch-001 epoch-002 --patterns-only

# Save analysis to file
python3 epoch_analyzer.py --epochs epoch-001 epoch-002 --output analysis.json
```

**Analysis Types:**
- **Trend Analysis**: Tracks metric changes over time (improving/declining/stable)
- **Task Progression**: Individual task performance consistency
- **Performance Patterns**: Identifies problematic tasks and improvement opportunities
- **Recommendations**: Actionable insights for evolution strategy

### 4. Unified CLI (`metrics_cli.py`)

Provides a single interface for all metrics operations.

**Usage:**
```bash
# Score operations
python3 metrics_cli.py score --epoch epoch-001
python3 metrics_cli.py score --epoch epoch-001 --task task-001
python3 metrics_cli.py score --epoch epoch-001 --validation-summary

# Report operations  
python3 metrics_cli.py report --epoch epoch-001
python3 metrics_cli.py report --compare epoch-001 epoch-002
python3 metrics_cli.py report --list-epochs

# Analysis operations
python3 metrics_cli.py analyze --epochs epoch-001 epoch-002 epoch-003
python3 metrics_cli.py analyze --epochs epoch-001 epoch-002 --trends-only
```

## Integration with Evaluation Pipeline

The metrics system integrates with the validation worker results:

1. **Validation Worker** executes code and runs tests, storing results in job artifacts
2. **Score Calculator** reads job queue and extracts scoring information
3. **Report Generator** creates comprehensive reports from calculated scores
4. **Epoch Analyzer** identifies trends and patterns across multiple epochs

## File Structure

```
evaluation/
├── metrics-collectors/
│   ├── __init__.py
│   ├── score_calculator.py     # Core scoring logic
│   ├── report_generator.py     # Report generation
│   ├── epoch_analyzer.py       # Advanced analysis
│   └── metrics_cli.py          # Unified CLI interface
├── test_metrics.py             # Test suite
└── METRICS_README.md           # This documentation
```

## Output Examples

### Task Score Output
```
Task Score for epoch-001/task-001:
  Status: completed
  Score: 2/2 (100.0%)
  Compilation: 1/1
  Tests: 1/1
```

### Epoch Score Output
```
Epoch Score for epoch-001:
  Total Score: 8/10 (80.0%)
  Tasks: 4/5 completed
  Compilation Success: 90.0%
  Test Success: 70.0%
```

### Trend Analysis Output
```
📈 Trend Analysis:
  📈 Overall Success Rate: +15.5% (improving)
  ➡️ Compilation Success Rate: +2.1% (stable)
  📉 Test Success Rate: -5.3% (declining)
```

## Generated Report Files

Reports are saved to appropriate directories:
- **Single Epoch**: `epochs/{epoch}/metrics/`
- **Comparisons**: `evaluation/reports/`

**JSON Report Structure:**
```json
{
  "metadata": {
    "epoch": "epoch-001",
    "generated_at": "2025-06-24T08:26:43Z",
    "report_version": "1.0"
  },
  "summary": {
    "total_score": 8,
    "max_possible_score": 10,
    "success_rate": 80.0,
    "compilation_success_rate": 90.0,
    "test_success_rate": 70.0
  },
  "task_details": { ... }
}
```

## Testing

Run the test suite to verify functionality:
```bash
python3 test_metrics.py
```

The test suite validates:
- Score calculation accuracy
- Report generation functionality  
- Analysis algorithm correctness
- Component integration

## Usage in Evolution Pipeline

The metrics system supports the evolution process by:

1. **Performance Tracking**: Monitor improvement across epochs
2. **Weakness Identification**: Find consistently problematic tasks
3. **Evolution Guidance**: Recommendations for next iteration focus
4. **Progress Validation**: Ensure evolution moves in positive direction

## Future Enhancements

Potential improvements include:
- Real-time metrics dashboard
- Automated alert system for performance regression
- Integration with external analysis tools
- Custom scoring algorithms for specific domains