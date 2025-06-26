#!/usr/bin/env python3
"""
Evaluate Epoch - orchestrate evaluation of an epoch against all default tasks
"""

import os
import sys
import json
import shutil
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from job_queue import JobQueue, JobType, JobStatus, JobResult
from config_simple import load_config

class EpochEvaluator:
    """Manages evaluation of an epoch against all default tasks"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        
        # Use runtime paths for job queue file
        self.base_dir = Path(__file__).parent.parent
        runtime_paths = self.config.get_runtime_paths(self.base_dir)
        job_queue_path = runtime_paths['state'] / self.config.job_queue_file
        
        self.job_queue = JobQueue(str(job_queue_path))
    
    def evaluate_epoch(self, epoch_name: str, parallel: bool = True, generate_metrics: bool = True) -> Dict[str, Any]:
        """
        Evaluate an epoch against all default tasks
        
        Args:
            epoch_name: Name of epoch to evaluate (e.g., 'epoch-001')
            parallel: Whether to run tasks in parallel
            generate_metrics: Whether to automatically generate comprehensive metrics
            
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
        
        # Enqueue validation jobs for completed tasks
        validation_job_ids = self._enqueue_validation_jobs(epoch_name, results)
        if validation_job_ids:
            print(f"🔍 Enqueued {len(validation_job_ids)} validation jobs")
            validation_results = self._monitor_validation_jobs(validation_job_ids)
        else:
            validation_results = {}
        
        # Generate summary
        summary = self._generate_evaluation_summary(epoch_name, results, validation_results)
        
        # Export job queue data for Evolution analysis
        print("💾 Exporting job queue data for Evolution analysis...")
        self._export_job_queue_data(epoch_name, results, validation_results)
        
        # Automatically generate metrics after evaluation is complete (if enabled)
        if generate_metrics:
            print("📊 Generating comprehensive metrics...")
            metrics_summary = self._generate_comprehensive_metrics(epoch_name)
            # Add metrics to the summary
            summary['metrics'] = metrics_summary
        else:
            print("📊 Skipping metrics generation (disabled)")
            summary['metrics'] = {'skipped': True, 'reason': 'Disabled by user'}
        
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
    
    def _enqueue_validation_jobs(self, epoch_name: str, evaluation_results: Dict[str, Any]) -> List[str]:
        """
        Enqueue validation jobs for successfully completed evaluation tasks
        
        Returns:
            List of validation job IDs
        """
        validation_job_ids = []
        
        for job_id, job in evaluation_results.items():
            # Only enqueue validation for successfully completed tasks
            if job.status == JobStatus.COMPLETED:
                task_name = job.parameters.get('task', 'unknown')
                
                # Enqueue validation job
                validation_job_id = self.job_queue.enqueue(
                    JobType.COMPILE_CHECK,
                    {
                        'epoch': epoch_name,
                        'task': task_name,
                        'evaluation_job_id': job_id  # Link back to original evaluation
                    },
                    max_retries=1
                )
                validation_job_ids.append(validation_job_id)
                print(f"   🔍 Enqueued validation for {task_name}: {validation_job_id[:8]}...")
        
        return validation_job_ids
    
    def _monitor_validation_jobs(self, job_ids: List[str], 
                                timeout_minutes: int = 15) -> Dict[str, Any]:
        """
        Monitor validation jobs until completion
        
        Returns:
            Dictionary mapping job_id to job results
        """
        print(f"⏱️  Monitoring {len(job_ids)} validation jobs (timeout: {timeout_minutes}min)")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        results = {}
        
        while time.time() - start_time < timeout_seconds:
            # Reload queue state to get fresh updates from workers
            self.job_queue.reload_from_file()
            
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
                        print(f"   ✅ Validation for {task_name} completed ({job_id[:8]}...)")
                    completed_jobs += 1
                elif job.status == JobStatus.FAILED:
                    if job_id not in results:
                        results[job_id] = job
                        task_name = job.parameters.get('task', 'unknown')
                        error = job.result.error if job.result else "Unknown error"
                        print(f"   ❌ Validation for {task_name} failed ({job_id[:8]}...): {error}")
                    failed_jobs += 1
                elif job.status == JobStatus.RUNNING:
                    running_jobs += 1
            
            # Check if all jobs are done
            if completed_jobs + failed_jobs == len(job_ids):
                print(f"🏁 All validation jobs completed: {completed_jobs} successful, {failed_jobs} failed")
                break
            
            # Status update
            if len(results) % 3 == 0 or running_jobs > 0:  # Update every 3 completions or when jobs running
                pending = len(job_ids) - completed_jobs - failed_jobs - running_jobs
                print(f"   📊 Validation status: {completed_jobs} done, {running_jobs} running, {failed_jobs} failed, {pending} pending")
            
            time.sleep(3)  # Poll every 3 seconds for validation (faster than evaluation)
        
        # Handle timeout
        if time.time() - start_time >= timeout_seconds:
            print(f"⚠️  Validation timeout reached after {timeout_minutes} minutes")
            
            # Mark remaining jobs
            for job_id in job_ids:
                if job_id not in results:
                    job = self.job_queue.get_job(job_id)
                    if job:
                        results[job_id] = job
        
        return results
    
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
            # Reload queue state to get fresh updates from workers
            self.job_queue.reload_from_file()
            
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
                                   results: Dict[str, Any],
                                   validation_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate evaluation summary from job results
        """
        print("📊 Generating evaluation summary...")
        
        if validation_results is None:
            validation_results = {}
        
        summary = {
            'epoch': epoch_name,
            'total_tasks': len(results),
            'successful_tasks': 0,
            'failed_tasks': 0,
            'validated_tasks': 0,
            'task_results': {},
            'overall_score': 0,
            'max_possible_score': len(results) * 3,  # 3 points per task (completion + compilation + tests)
            'success_rate': 0.0,
            'validation_summary': {
                'total_validation_jobs': len(validation_results),
                'successful_validations': 0,
                'failed_validations': 0
            }
        }
        
        # Create a mapping from task names to validation jobs
        validation_by_task = {}
        for val_job_id, val_job in validation_results.items():
            task_name = val_job.parameters.get('task', 'unknown')
            validation_by_task[task_name] = val_job
        
        for job_id, job in results.items():
            task_name = job.parameters.get('task', 'unknown')
            
            if job.status == JobStatus.COMPLETED:
                summary['successful_tasks'] += 1
                output = job.result.output if job.result else "No output"
                
                # Base task result
                task_result = {
                    'status': 'completed',
                    'job_id': job_id,
                    'output': output,
                    'execution_time': job.result.execution_time if job.result else 0,
                    'task_completion_score': 1,  # 1 point for completing the task
                    'compilation_score': 0,
                    'test_score': 0,
                    'total_score': 1,  # Start with 1 point for completion
                    'validation_status': 'pending'
                }
                
                # Add validation results if available
                if task_name in validation_by_task:
                    val_job = validation_by_task[task_name]
                    summary['validated_tasks'] += 1
                    
                    if val_job.status == JobStatus.COMPLETED and val_job.result and val_job.result.artifacts:
                        summary['validation_summary']['successful_validations'] += 1
                        artifacts = val_job.result.artifacts
                        
                        task_result['compilation_score'] = artifacts.get('compilation_score', 0)
                        task_result['test_score'] = artifacts.get('test_score', 0)
                        task_result['total_score'] = (task_result['task_completion_score'] + 
                                                     task_result['compilation_score'] + 
                                                     task_result['test_score'])
                        task_result['validation_status'] = 'completed'
                        task_result['validation_job_id'] = val_job.id
                        
                        summary['overall_score'] += task_result['total_score']
                    else:
                        summary['validation_summary']['failed_validations'] += 1
                        task_result['validation_status'] = 'failed'
                        error = val_job.result.error if val_job.result else "Validation failed"
                        task_result['validation_error'] = error
                        # Only count task completion point if validation failed
                        summary['overall_score'] += 1
                else:
                    task_result['validation_status'] = 'not_run'
                    # Only count task completion point if no validation
                    summary['overall_score'] += 1
                
                summary['task_results'][task_name] = task_result
            else:
                summary['failed_tasks'] += 1
                error = job.result.error if job.result else "Unknown error"
                
                summary['task_results'][task_name] = {
                    'status': 'failed',
                    'job_id': job_id,
                    'error': error,
                    'task_completion_score': 0,
                    'compilation_score': 0,
                    'test_score': 0,
                    'total_score': 0,
                    'validation_status': 'not_applicable'
                }
        
        summary['success_rate'] = (summary['overall_score'] / summary['max_possible_score']) * 100 if summary['max_possible_score'] > 0 else 0
        
        # Print summary
        print(f"📈 Evaluation Summary for {epoch_name}:")
        print(f"   Tasks: {summary['successful_tasks']}/{summary['total_tasks']} completed ({summary['successful_tasks']/summary['total_tasks']*100:.1f}%)")
        print(f"   Validation: {summary['validated_tasks']}/{summary['successful_tasks']} tasks validated")
        print(f"   Overall Score: {summary['overall_score']}/{summary['max_possible_score']} ({summary['success_rate']:.1f}%)")
        
        if summary['validated_tasks'] > 0:
            print(f"   ✅ Scoring complete with validation results")
        
        return summary
    
    def _export_job_queue_data(self, epoch_name: str, 
                              evaluation_results: Dict[str, Any], 
                              validation_results: Dict[str, Any]) -> None:
        """
        Export detailed job queue data to metrics folder for Evolution analysis
        """
        try:
            # Create metrics directory
            metrics_dir = self.base_dir / "epochs" / epoch_name / "metrics"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect all relevant job data
            job_export_data = {
                'epoch': epoch_name,
                'exported_at': datetime.now().isoformat(),
                'evaluation_jobs': {},
                'validation_jobs': {},
                'job_queue_summary': {
                    'total_evaluation_jobs': len(evaluation_results),
                    'total_validation_jobs': len(validation_results),
                    'successful_evaluations': sum(1 for job in evaluation_results.values() if job.status.value == 'completed'),
                    'successful_validations': sum(1 for job in validation_results.values() if job.status.value == 'completed')
                }
            }
            
            # Export evaluation job details
            for job_id, job in evaluation_results.items():
                task_name = job.parameters.get('task', 'unknown')
                job_export_data['evaluation_jobs'][task_name] = {
                    'job_id': job_id,
                    'status': job.status.value,
                    'parameters': job.parameters,
                    'created_at': job.created_at,
                    'started_at': job.started_at,
                    'completed_at': job.completed_at,
                    'execution_time': job.result.execution_time if job.result else 0,
                    'success': job.result.success if job.result else False,
                    'output': job.result.output if job.result else "",
                    'error': job.result.error if job.result else "",
                    'output_files': job.result.artifacts.get('output_files', []) if job.result and job.result.artifacts else [],
                    'return_code': job.result.artifacts.get('return_code') if job.result and job.result.artifacts else None,
                    'retry_count': getattr(job, 'retry_count', 0)
                }
            
            # Export validation job details (with cleaner Docker logs)
            for job_id, job in validation_results.items():
                task_name = job.parameters.get('task', 'unknown')
                validation_data = {
                    'job_id': job_id,
                    'evaluation_job_id': job.parameters.get('evaluation_job_id'),
                    'status': job.status.value,
                    'parameters': job.parameters,
                    'created_at': job.created_at,
                    'started_at': job.started_at,
                    'completed_at': job.completed_at,
                    'execution_time': job.result.execution_time if job.result else 0,
                    'success': job.result.success if job.result else False,
                    'compilation_score': 0,
                    'test_score': 0,
                    'total_score': 0,
                    'validation_method': 'docker-compose'
                }
                
                if job.result and job.result.artifacts:
                    artifacts = job.result.artifacts
                    validation_data.update({
                        'compilation_score': artifacts.get('compilation_score', 0),
                        'test_score': artifacts.get('test_score', 0), 
                        'total_score': artifacts.get('total_score', 0),
                        'total_files': artifacts.get('total_files', 0),
                        'output_files': artifacts.get('output_files', []),
                        'validation_method': artifacts.get('validation_method', 'docker-compose'),
                        # Clean up Docker logs - keep only essential info
                        'compile_success': artifacts.get('compilation_score', 0) > 0,
                        'test_success': artifacts.get('test_score', 0) > 0,
                        'compile_logs': self._clean_docker_logs(artifacts.get('compile_stdout', '')),
                        'test_logs': self._clean_docker_logs(artifacts.get('test_stdout', '')),
                        'errors': artifacts.get('compile_stderr', '') + artifacts.get('test_stderr', '')
                    })
                
                job_export_data['validation_jobs'][task_name] = validation_data
            
            # Save to file
            export_file = metrics_dir / f"{epoch_name}_job_data.json"
            with open(export_file, 'w') as f:
                json.dump(job_export_data, f, indent=2, default=str)
            
            print(f"   💾 Job queue data exported to: {export_file.name}")
            
        except Exception as e:
            print(f"   ⚠️  Failed to export job queue data: {e}")
    
    def _clean_docker_logs(self, logs: str) -> str:
        """
        Clean up Docker logs by removing verbose formatting and keeping only essential information
        """
        if not logs:
            return ""
        
        lines = logs.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines and Docker formatting noise
            if (not line.strip() or 
                line.startswith('#') or 
                'sha256:' in line or 
                'transferring' in line or 
                'CACHED' in line or
                'exporting layers' in line or
                'naming to docker.io' in line):
                continue
            
            # Keep test results, compilation results, and error messages
            if any(keyword in line for keyword in [
                'FAILED', 'PASSED', 'ERROR', 'WARNING', 
                'test session starts', 'failed in', 'passed in',
                'ModuleNotFoundError', 'ImportError', 'SyntaxError',
                'collected', 'items']):
                cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines[:20])  # Keep max 20 relevant lines
    
    def _generate_comprehensive_metrics(self, epoch_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive metrics using the metrics system
        
        Returns:
            Dictionary with all metrics and reports
        """
        try:
            # Import metrics modules
            sys.path.insert(0, str(self.base_dir / "evaluation" / "metrics-collectors"))
            from score_calculator import ScoreCalculator
            from report_generator import ReportGenerator
            from epoch_analyzer import EpochAnalyzer
            
            # Initialize metrics components
            calculator = ScoreCalculator()
            report_generator = ReportGenerator()
            analyzer = EpochAnalyzer()
            
            metrics_summary = {
                'epoch_name': epoch_name,
                'generated_at': datetime.now().isoformat(),
                'score_summary': None,
                'detailed_report': None,
                'analysis': None,
                'reports_generated': []
            }
            
            print(f"   📊 Calculating epoch scores...")
            try:
                # Calculate epoch score
                epoch_score = calculator.calculate_epoch_score(epoch_name)
                metrics_summary['score_summary'] = {
                    'total_score': epoch_score.total_score,
                    'max_possible_score': epoch_score.max_possible_score,
                    'success_rate': epoch_score.success_rate,
                    'completed_tasks': epoch_score.completed_tasks,
                    'total_tasks': epoch_score.total_tasks,
                    'compilation_success_rate': epoch_score.compilation_success_rate,
                    'test_success_rate': epoch_score.test_success_rate
                }
                print(f"   ✅ Score: {epoch_score.total_score}/{epoch_score.max_possible_score} ({epoch_score.success_rate:.1f}%)")
            except Exception as e:
                print(f"   ⚠️  Score calculation failed: {e}")
                metrics_summary['score_summary'] = {'error': str(e)}
            
            print(f"   📋 Generating detailed reports...")
            try:
                # Generate detailed report (this already saves files and returns paths)
                report_files = report_generator.generate_epoch_report(epoch_name)
                metrics_summary['detailed_report'] = report_files
                
                # Add generated files to the list
                for format_type, file_path in report_files.items():
                    metrics_summary['reports_generated'].append(file_path)
                    print(f"   💾 Saved {format_type.upper()} report: {Path(file_path).name}")
                
            except Exception as e:
                print(f"   ⚠️  Report generation failed: {e}")
                metrics_summary['detailed_report'] = {'error': str(e)}
            
            print(f"   🔍 Analyzing epoch performance...")
            try:
                # Perform epoch analysis
                analysis_data = analyzer.analyze_epoch(epoch_name)
                metrics_summary['analysis'] = analysis_data
                print(f"   ✅ Analysis complete")
            except Exception as e:
                print(f"   ⚠️  Analysis failed: {e}")
                metrics_summary['analysis'] = {'error': str(e)}
            
            print(f"   🎯 Metrics generation complete!")
            print(f"      - Score: {metrics_summary.get('score_summary', {}).get('success_rate', 'N/A')}% success rate")
            print(f"      - Reports: {len(metrics_summary['reports_generated'])} files generated")
            
            return metrics_summary
            
        except ImportError as e:
            print(f"   ⚠️  Metrics system not available: {e}")
            return {
                'error': f"Metrics system not available: {e}",
                'epoch_name': epoch_name,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"   ❌ Metrics generation failed: {e}")
            return {
                'error': f"Metrics generation failed: {e}",
                'epoch_name': epoch_name,
                'generated_at': datetime.now().isoformat()
            }

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
    parser.add_argument("--no-metrics", action="store_true",
                       help="Skip automatic metrics generation (evaluation only)")
    
    args = parser.parse_args()
    
    # Handle parallel/sequential flags
    parallel = args.parallel and not args.sequential
    generate_metrics = not args.no_metrics
    
    try:
        evaluator = EpochEvaluator(args.config)
        summary = evaluator.evaluate_epoch(args.epoch, parallel, generate_metrics)
        
        print(f"\n🎉 Evaluation of {args.epoch} completed!")
        print(f"📊 Results summary: {summary['successful_tasks']}/{summary['total_tasks']} tasks completed")
        
        # Show metrics summary if available
        if 'metrics' in summary and summary['metrics'].get('score_summary'):
            metrics = summary['metrics']['score_summary']
            print(f"📈 Final Score: {metrics.get('total_score', 'N/A')}/{metrics.get('max_possible_score', 'N/A')} ({metrics.get('success_rate', 0):.1f}%)")
            print(f"🧪 Test Success: {metrics.get('test_success_rate', 0):.1f}%")
            print(f"⚙️  Compilation Success: {metrics.get('compilation_success_rate', 0):.1f}%")
            
            if summary['metrics'].get('reports_generated'):
                print(f"📋 Generated {len(summary['metrics']['reports_generated'])} detailed reports")
        
        # Save summary to file
        import json
        summary_file = Path(__file__).parent.parent / "epochs" / args.epoch / "evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"💾 Complete summary saved to: {summary_file}")
        
        print(f"\n✨ {args.epoch} evaluation is fully self-contained - all tasks, validation, and metrics complete!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()