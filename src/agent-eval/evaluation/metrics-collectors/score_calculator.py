#!/usr/bin/env python3
"""
Score Calculator - aggregates validation results into task and epoch scores
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from job_queue import JobQueue, JobType, JobStatus
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
    output_files: List[str] = None
    error_message: str = None
    job_id: str = None
    validation_job_id: str = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        self.success_rate = (self.total_score / self.max_possible_score) * 100 if self.max_possible_score > 0 else 0.0

@dataclass 
class EpochScore:
    """Aggregated score for an entire epoch"""
    epoch: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    
    total_score: int = 0
    max_possible_score: int = 0
    success_rate: float = 0.0
    
    compilation_success_rate: float = 0.0
    test_success_rate: float = 0.0
    
    task_scores: Dict[str, TaskScore] = None
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.task_scores is None:
            self.task_scores = {}
        if self.generated_at is None:
            self.generated_at = datetime.now()
        
        # Calculate success rate
        self.success_rate = (self.total_score / self.max_possible_score) * 100 if self.max_possible_score > 0 else 0.0

class ScoreCalculator:
    """Calculates and aggregates scores from validation results"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.job_queue = JobQueue(self.config.job_queue_file)
        self.base_dir = Path(__file__).parent.parent.parent
    
    def calculate_task_score(self, epoch: str, task_name: str) -> TaskScore:
        """
        Calculate score for a single task by examining evaluation summary and job results
        """
        # First try to read from evaluation summary file (preferred method)
        evaluation_summary = self._load_evaluation_summary(epoch)
        if evaluation_summary and task_name in evaluation_summary.get('task_results', {}):
            task_data = evaluation_summary['task_results'][task_name]
            
            task_score = TaskScore(
                task_name=task_name,
                epoch=epoch,
                task_completion_score=task_data.get('task_completion_score', 0),
                compilation_score=task_data.get('compilation_score', 0),
                test_score=task_data.get('test_score', 0),
                total_score=task_data.get('total_score', 0),
                status=task_data.get('status', 'unknown'),
                execution_time=task_data.get('execution_time', 0.0),
                job_id=task_data.get('job_id'),
                validation_job_id=task_data.get('validation_job_id')
            )
            
            if 'error' in task_data:
                task_score.error_message = task_data['error']
            elif 'validation_error' in task_data:
                task_score.error_message = task_data['validation_error']
                
            return task_score
        
        # Fallback: Find evaluation job for this task (legacy method)
        evaluation_job = self._find_evaluation_job(epoch, task_name)
        if not evaluation_job:
            return TaskScore(
                task_name=task_name,
                epoch=epoch,
                status="missing_evaluation",
                error_message="No evaluation job found"
            )
        
        task_score = TaskScore(
            task_name=task_name,
            epoch=epoch,
            job_id=evaluation_job.id
        )
        
        # Check if evaluation was successful
        if evaluation_job.status != JobStatus.COMPLETED:
            task_score.status = "failed"
            if evaluation_job.result:
                task_score.error_message = evaluation_job.result.error
            return task_score
        
        # Task completed successfully - give 1 point for completion
        task_score.task_completion_score = 1
        task_score.status = "completed"
        
        # Look for validation job results
        validation_job = self._find_validation_job(epoch, task_name)
        if not validation_job:
            task_score.total_score = 1  # Only task completion point
            task_score.error_message = "Task completed but no validation job found"
            return task_score
        
        if validation_job.status != JobStatus.COMPLETED:
            task_score.total_score = 1  # Only task completion point
            if validation_job.result:
                task_score.error_message = f"Validation failed: {validation_job.result.error}"
            return task_score
        
        # Extract scores from validation artifacts
        if validation_job.result and validation_job.result.artifacts:
            artifacts = validation_job.result.artifacts
            task_score.compilation_score = artifacts.get('compilation_score', 0)
            task_score.test_score = artifacts.get('test_score', 0)
            task_score.total_score = (task_score.task_completion_score + 
                                     task_score.compilation_score + 
                                     task_score.test_score)
            task_score.output_files = artifacts.get('output_files', [])
            task_score.execution_time = validation_job.result.execution_time or 0.0
            task_score.validation_job_id = validation_job.id
        else:
            task_score.total_score = 1  # Only task completion point
            task_score.error_message = "Validation completed but no scoring artifacts found"
        
        return task_score
    
    def calculate_epoch_score(self, epoch: str, task_names: List[str] = None) -> EpochScore:
        """
        Calculate aggregated score for an entire epoch
        """
        if task_names is None:
            task_names = self._discover_epoch_tasks(epoch)
        
        epoch_score = EpochScore(
            epoch=epoch,
            total_tasks=len(task_names),
            max_possible_score=len(task_names) * 2  # 2 points per task
        )
        
        compilation_successes = 0
        test_successes = 0
        
        for task_name in task_names:
            task_score = self.calculate_task_score(epoch, task_name)
            epoch_score.task_scores[task_name] = task_score
            
            if task_score.status == "completed":
                epoch_score.completed_tasks += 1
                epoch_score.total_score += task_score.total_score
                
                if task_score.compilation_score > 0:
                    compilation_successes += 1
                if task_score.test_score > 0:
                    test_successes += 1
                    
            elif task_score.status in ["failed", "validation_failed"]:
                epoch_score.failed_tasks += 1
            else:
                epoch_score.pending_tasks += 1
        
        # Calculate success rates
        if epoch_score.completed_tasks > 0:
            epoch_score.compilation_success_rate = (compilation_successes / epoch_score.completed_tasks) * 100
            epoch_score.test_success_rate = (test_successes / epoch_score.completed_tasks) * 100
        
        return epoch_score
    
    def _find_evaluation_job(self, epoch: str, task_name: str):
        """Find the evaluation job for a specific task"""
        # In a real implementation, we'd query the job queue more efficiently
        # For now, we'll iterate through all jobs
        for job_id, job in self.job_queue.jobs.items():
            if (job.job_type == JobType.EVALUATE_TASK and 
                job.parameters.get('epoch') == epoch and
                job.parameters.get('task') == task_name):
                return job
        return None
    
    def _find_validation_job(self, epoch: str, task_name: str):
        """Find the validation job for a specific task"""
        for job_id, job in self.job_queue.jobs.items():
            if (job.job_type == JobType.COMPILE_CHECK and 
                job.parameters.get('epoch') == epoch and
                job.parameters.get('task') == task_name):
                return job
        return None
    
    def _discover_epoch_tasks(self, epoch: str) -> List[str]:
        """Discover all tasks that were run for an epoch"""
        epoch_runs_dir = self.base_dir / "epochs" / epoch / "runs"
        if not epoch_runs_dir.exists():
            return []
        
        task_dirs = [d.name for d in epoch_runs_dir.iterdir() 
                    if d.is_dir() and d.name.startswith('task-')]
        return sorted(task_dirs)
    
    def get_validation_summary(self, epoch: str) -> Dict[str, Any]:
        """Get a summary of validation status for debugging"""
        epoch_score = self.calculate_epoch_score(epoch)
        
        summary = {
            'epoch': epoch,
            'validation_summary': {
                'total_tasks': epoch_score.total_tasks,
                'completed_validations': epoch_score.completed_tasks,
                'failed_validations': epoch_score.failed_tasks,
                'pending_validations': epoch_score.pending_tasks,
            },
            'validation_details': {}
        }
        
        for task_name, task_score in epoch_score.task_scores.items():
            summary['validation_details'][task_name] = {
                'status': task_score.status,
                'score': f"{task_score.total_score}/3",
                'task_completion': bool(task_score.task_completion_score),
                'compilation': bool(task_score.compilation_score),
                'tests': bool(task_score.test_score),
                'error': task_score.error_message
            }
        
        return summary
    
    def _load_evaluation_summary(self, epoch: str) -> Optional[Dict[str, Any]]:
        """Load evaluation summary from file if it exists"""
        summary_file = self.base_dir / "epochs" / epoch / "evaluation_summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load evaluation summary: {e}")
        return None

def main():
    """CLI interface for score calculation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate scores for epoch evaluation")
    parser.add_argument("--epoch", required=True, help="Epoch name (e.g., epoch-001)")
    parser.add_argument("--task", help="Specific task name (optional)")
    parser.add_argument("--validation-summary", action="store_true", 
                       help="Show validation status summary")
    
    args = parser.parse_args()
    
    calculator = ScoreCalculator()
    
    if args.validation_summary:
        summary = calculator.get_validation_summary(args.epoch)
        print(json.dumps(summary, indent=2, default=str))
        return
    
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
            status_icon = "✅" if task_score.status == "completed" else "❌"
            print(f"  {status_icon} {task_name}: {task_score.total_score}/3 ({task_score.status})")

if __name__ == "__main__":
    main()