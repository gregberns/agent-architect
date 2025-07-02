#!/usr/bin/env python3
"""
Score Calculator - aggregates validation results into task and epoch scores
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from config_simple import load_config

@dataclass
class TaskScore:
    """Score for a single task"""
    task_name: str
    epoch: str
    task_completion_score: int = 0  # 1 point for completing the task
    compilation_score: int = 0      # 1 point for compilation success
    test_score: int = 0             # 1 point for tests passing
    total_score: int = 0
    max_possible_score: int = 3     # Updated to 3-point system
    success_rate: float = 0.0
    status: str = "pending"  # pending, completed, failed, missing_validation
    execution_time: float = 0.0
    error_message: Optional[str] = None

    def __post_init__(self):
        self.total_score = self.task_completion_score + self.compilation_score + self.test_score
        self.success_rate = (self.total_score / self.max_possible_score) * 100 if self.max_possible_score > 0 else 0.0

@dataclass 
class EpochScore:
    """Aggregated score for an entire epoch"""
    epoch: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    total_score: int = 0
    max_possible_score: int = 0
    success_rate: float = 0.0
    
    compilation_success_rate: float = 0.0
    test_success_rate: float = 0.0
    
    task_scores: Dict[str, TaskScore] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def calculate_final_metrics(self):
        """Calculate aggregated metrics after all tasks are scored."""
        if self.total_tasks > 0:
            self.max_possible_score = self.total_tasks * 3
            self.success_rate = (self.total_score / self.max_possible_score) * 100 if self.max_possible_score > 0 else 0.0
            
            compilation_successes = sum(1 for ts in self.task_scores.values() if ts.compilation_score > 0)
            test_successes = sum(1 for ts in self.task_scores.values() if ts.test_score > 0)
            
            # Base success rate on completed tasks to be more representative
            if self.completed_tasks > 0:
                self.compilation_success_rate = (compilation_successes / self.completed_tasks) * 100
                self.test_success_rate = (test_successes / self.completed_tasks) * 100

class ScoreCalculator:
    """Calculates and aggregates scores from evaluation summary"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.base_dir = Path(__file__).parent.parent.parent
    
    def calculate_task_score(self, epoch: str, task_name: str) -> TaskScore:
        """
        Calculate score for a single task by examining the evaluation summary.
        """
        evaluation_summary = self._load_evaluation_summary(epoch)
        if not evaluation_summary or task_name not in evaluation_summary.get('task_results', {}):
            return TaskScore(
                task_name=task_name,
                epoch=epoch,
                status="missing_evaluation",
                error_message="No evaluation summary found or task not in summary"
            )
            
        task_data = evaluation_summary['task_results'][task_name]
        
        return TaskScore(
            task_name=task_name,
            epoch=epoch,
            task_completion_score=task_data.get('task_completion_score', 0),
            compilation_score=task_data.get('compilation_score', 0),
            test_score=task_data.get('test_score', 0),
            status=task_data.get('status', 'unknown'),
            execution_time=task_data.get('execution_time', 0.0),
            error_message=task_data.get('error')
        )
    
    def calculate_epoch_score(self, epoch: str) -> EpochScore:
        """
        Calculate aggregated score for an entire epoch from the evaluation summary.
        """
        evaluation_summary = self._load_evaluation_summary(epoch)
        if not evaluation_summary:
            raise FileNotFoundError(f"Could not find or load evaluation_summary.json for epoch {epoch}")

        task_names = list(evaluation_summary.get('task_results', {}).keys())
        
        epoch_score = EpochScore(
            epoch=epoch,
            total_tasks=len(task_names)
        )
        
        for task_name in task_names:
            task_score = self.calculate_task_score(epoch, task_name)
            epoch_score.task_scores[task_name] = task_score
            
            if task_score.status == "completed":
                epoch_score.completed_tasks += 1
            else:
                epoch_score.failed_tasks += 1
            
            epoch_score.total_score += task_score.total_score
        
        epoch_score.calculate_final_metrics()
        return epoch_score
    
    def _load_evaluation_summary(self, epoch: str) -> Optional[Dict[str, Any]]:
        """Load evaluation summary from file if it exists"""
        summary_file = self.base_dir / "epochs" / epoch / "validation" / "evaluation_summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load or parse evaluation summary '{summary_file}': {e}")
        return None

def main():
    """CLI interface for score calculation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate scores for epoch evaluation")
    parser.add_argument("--epoch", required=True, help="Epoch name (e.g., epoch-001)")
    parser.add_argument("--task", help="Specific task name (optional)")
    
    args = parser.parse_args()
    
    calculator = ScoreCalculator()
    
    try:
        if args.task:
            # Calculate single task score
            task_score = calculator.calculate_task_score(args.epoch, args.task)
            print(f"Task Score for {args.epoch}/{args.task}:")
            print(f"  Status: {task_score.status}")
            print(f"  Score: {task_score.total_score}/3 ({task_score.success_rate:.1f}%)")
            print(f"  Task Completion: {task_score.task_completion_score}/1")
            print(f"  Compilation: {task_score.compilation_score}/1")
            print(f"  Tests: {task_score.test_score}/1")
            if task_score.error_message:
                print(f"  Error: {task_score.error_message}")
        else:
            # Calculate epoch score
            epoch_score = calculator.calculate_epoch_score(args.epoch)
            print(f"Epoch Score for {args.epoch}:")
            print(f"  Total Score: {epoch_score.total_score}/{epoch_score.max_possible_score} ({epoch_score.success_rate:.1f}%)")
            print(f"  Tasks: {epoch_score.completed_tasks}/{epoch_score.total_tasks} completed")
            print(f"  Compilation Success: {epoch_score.compilation_success_rate:.1f}%")
            print(f"  Test Success: {epoch_score.test_success_rate:.1f}%")
            
            print(f"\nTask Breakdown:")
            for task_name, task_score in epoch_score.task_scores.items():
                status_icon = "✅" if task_score.status == "completed" and task_score.total_score == 3 else "❌"
                print(f"  {status_icon} {task_name}: {task_score.total_score}/3 ({task_score.status})")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please run an evaluation for this epoch first.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
