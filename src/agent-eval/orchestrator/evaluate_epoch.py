#!/usr/bin/env python3
"""
Evaluate Epoch - orchestrate evaluation of an epoch against all default tasks
"""

import os
import sys
import shutil
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobStatus, JobResult
from config_simple import load_config

class EpochEvaluator:
    """Manages evaluation of an epoch against all default tasks"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.job_queue = JobQueue(self.config.job_queue_file)
        self.base_dir = Path(__file__).parent.parent
    
    def evaluate_epoch(self, epoch_name: str, parallel: bool = True) -> Dict[str, Any]:
        """
        Evaluate an epoch against all default tasks
        
        Args:
            epoch_name: Name of epoch to evaluate (e.g., 'epoch-001')
            parallel: Whether to run tasks in parallel
            
        Returns:
            Dictionary with evaluation results
        """
        print(f"🔍 Starting evaluation of {epoch_name}")
        
        # Validate epoch exists
        epoch_dir = self.base_dir / "epochs" / epoch_name
        if not epoch_dir.exists():
            raise ValueError(f"Epoch directory not found: {epoch_dir}")
        
        agent_src = epoch_dir / "agent-src"
        if not agent_src.exists():
            raise ValueError(f"Agent source not found: {agent_src}")
        
        # Setup tasks
        task_jobs = self._setup_tasks(epoch_name)
        if not task_jobs:
            raise ValueError("No tasks found to evaluate")
        
        print(f"📋 Setup {len(task_jobs)} tasks for evaluation")
        
        # Enqueue evaluation jobs
        job_ids = self._enqueue_evaluation_jobs(epoch_name, task_jobs, parallel)
        print(f"⚡ Enqueued {len(job_ids)} evaluation jobs")
        
        # Monitor completion if running in parallel
        if parallel:
            results = self._monitor_evaluation_jobs(job_ids)
        else:
            results = self._run_sequential_evaluation(epoch_name, task_jobs)
        
        # Generate summary
        summary = self._generate_evaluation_summary(epoch_name, results)
        
        return summary
    
    def _setup_tasks(self, epoch_name: str) -> List[str]:
        """
        Copy default workspaces to epoch runs directory
        
        Returns:
            List of task names that were set up
        """
        print("📁 Setting up tasks...")
        
        default_workspaces = self.base_dir / "default-workspaces"
        epoch_runs = self.base_dir / "epochs" / epoch_name / "runs"
        
        if not default_workspaces.exists():
            raise ValueError(f"Default workspaces not found: {default_workspaces}")
        
        # Create runs directory if it doesn't exist
        epoch_runs.mkdir(parents=True, exist_ok=True)
        
        # Get all task directories
        task_dirs = [d for d in default_workspaces.iterdir() 
                    if d.is_dir() and d.name.startswith('task-')]
        
        if not task_dirs:
            raise ValueError("No task directories found in default workspaces")
        
        task_names = []
        for task_dir in task_dirs:
            task_name = task_dir.name
            target_dir = epoch_runs / task_name
            
            # Remove existing task directory if it exists
            if target_dir.exists():
                print(f"   🔄 Updating existing {task_name}")
                shutil.rmtree(target_dir)
            else:
                print(f"   📋 Setting up {task_name}")
            
            # Copy task directory
            shutil.copytree(task_dir, target_dir)
            
            # Create output directory
            output_dir = target_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            task_names.append(task_name)
        
        print(f"✅ Set up {len(task_names)} tasks: {', '.join(task_names)}")
        return task_names
    
    def _enqueue_evaluation_jobs(self, epoch_name: str, task_names: List[str], 
                                parallel: bool) -> List[str]:
        """
        Enqueue evaluation jobs for all tasks
        
        Returns:
            List of job IDs
        """
        job_ids = []
        
        for task_name in task_names:
            # Enqueue task evaluation job
            job_id = self.job_queue.enqueue(
                JobType.EVALUATE_TASK,
                {
                    'epoch': epoch_name,
                    'task': task_name,
                    'evaluation_run': True
                },
                max_retries=2
            )
            job_ids.append(job_id)
            print(f"   📤 Enqueued {task_name}: {job_id[:8]}...")
        
        return job_ids
    
    def _monitor_evaluation_jobs(self, job_ids: List[str], 
                                timeout_minutes: int = 30) -> Dict[str, Any]:
        """
        Monitor evaluation jobs until completion
        
        Returns:
            Dictionary mapping job_id to job results
        """
        print(f"⏱️  Monitoring {len(job_ids)} jobs (timeout: {timeout_minutes}min)")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        results = {}
        
        while time.time() - start_time < timeout_seconds:
            # Check status of all jobs
            completed_jobs = 0
            running_jobs = 0
            failed_jobs = 0
            
            for job_id in job_ids:
                job = self.job_queue.get_job(job_id)
                if not job:
                    continue
                
                if job.status == JobStatus.COMPLETED:
                    if job_id not in results:
                        results[job_id] = job
                        task_name = job.parameters.get('task', 'unknown')
                        print(f"   ✅ {task_name} completed ({job_id[:8]}...)")
                    completed_jobs += 1
                elif job.status == JobStatus.FAILED:
                    if job_id not in results:
                        results[job_id] = job
                        task_name = job.parameters.get('task', 'unknown')
                        error = job.result.error if job.result else "Unknown error"
                        print(f"   ❌ {task_name} failed ({job_id[:8]}...): {error}")
                    failed_jobs += 1
                elif job.status == JobStatus.RUNNING:
                    running_jobs += 1
            
            # Check if all jobs are done
            if completed_jobs + failed_jobs == len(job_ids):
                print(f"🏁 All jobs completed: {completed_jobs} successful, {failed_jobs} failed")
                break
            
            # Status update
            if len(results) % 5 == 0 or running_jobs > 0:  # Update every 5 completions or when jobs running
                pending = len(job_ids) - completed_jobs - failed_jobs - running_jobs
                print(f"   📊 Status: {completed_jobs} done, {running_jobs} running, {failed_jobs} failed, {pending} pending")
            
            time.sleep(5)  # Poll every 5 seconds
        
        # Handle timeout
        if time.time() - start_time >= timeout_seconds:
            print(f"⚠️  Timeout reached after {timeout_minutes} minutes")
            
            # Mark remaining jobs
            for job_id in job_ids:
                if job_id not in results:
                    job = self.job_queue.get_job(job_id)
                    if job:
                        results[job_id] = job
        
        return results
    
    def _run_sequential_evaluation(self, epoch_name: str, task_names: List[str]) -> Dict[str, Any]:
        """
        Run evaluation sequentially (not implemented for now)
        """
        print("⚠️  Sequential evaluation not implemented, defaulting to parallel")
        job_ids = self._enqueue_evaluation_jobs(epoch_name, task_names, True)
        return self._monitor_evaluation_jobs(job_ids)
    
    def _generate_evaluation_summary(self, epoch_name: str, 
                                   results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate evaluation summary from job results
        """
        print("📊 Generating evaluation summary...")
        
        summary = {
            'epoch': epoch_name,
            'total_tasks': len(results),
            'successful_tasks': 0,
            'failed_tasks': 0,
            'task_results': {},
            'overall_score': 0,
            'max_possible_score': len(results) * 2,  # 2 points per task
            'success_rate': 0.0
        }
        
        for job_id, job in results.items():
            task_name = job.parameters.get('task', 'unknown')
            
            if job.status == JobStatus.COMPLETED:
                summary['successful_tasks'] += 1
                output = job.result.output if job.result else "No output"
                
                # Task completed successfully - will need validation for scoring
                summary['task_results'][task_name] = {
                    'status': 'completed',
                    'job_id': job_id,
                    'output': output,
                    'execution_time': job.result.execution_time if job.result else 0,
                    'needs_validation': True
                }
            else:
                summary['failed_tasks'] += 1
                error = job.result.error if job.result else "Unknown error"
                
                summary['task_results'][task_name] = {
                    'status': 'failed',
                    'job_id': job_id,
                    'error': error,
                    'needs_validation': False
                }
        
        summary['success_rate'] = summary['successful_tasks'] / summary['total_tasks'] * 100
        
        # Print summary
        print(f"📈 Evaluation Summary for {epoch_name}:")
        print(f"   Tasks: {summary['successful_tasks']}/{summary['total_tasks']} successful ({summary['success_rate']:.1f}%)")
        print(f"   Note: Scoring requires validation phase")
        
        return summary

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Evaluate an epoch against all default tasks")
    parser.add_argument("--epoch", required=True, help="Epoch name to evaluate (e.g., epoch-001)")
    parser.add_argument("--parallel", action="store_true", default=True, 
                       help="Run tasks in parallel (default: True)")
    parser.add_argument("--sequential", action="store_true", 
                       help="Run tasks sequentially (overrides --parallel)")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--timeout", type=int, default=30, 
                       help="Timeout in minutes for monitoring jobs (default: 30)")
    
    args = parser.parse_args()
    
    # Handle parallel/sequential flags
    parallel = args.parallel and not args.sequential
    
    try:
        evaluator = EpochEvaluator(args.config)
        summary = evaluator.evaluate_epoch(args.epoch, parallel)
        
        print(f"\n🎉 Evaluation of {args.epoch} completed!")
        print(f"Results summary: {summary['successful_tasks']}/{summary['total_tasks']} tasks completed")
        
        # Save summary to file
        import json
        summary_file = Path(__file__).parent.parent / "epochs" / args.epoch / "evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"📁 Summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()