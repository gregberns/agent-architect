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
import subprocess
import traceback
import multiprocessing
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_simple import load_config

# --- Worker Functions ---
# These functions must be at the top level for multiprocessing to pickle them.

def run_evaluation_task(args: Tuple[str, str, Path, int]) -> Dict[str, Any]:
    """
    Worker function to execute a single task evaluation using Docker.
    This replaces the old task-worker.py.
    """
    epoch_name, task_name, base_dir, timeout_seconds = args
    task_start_time = time.time()
    
    # Create unique identifiers for Docker resources
    unique_id = f"{epoch_name}-{task_name}-{int(task_start_time)}"
    image_tag = f"agent-eval-{unique_id}"
    container_name = f"agent-eval-{unique_id}"
    
    result = {
        'epoch_name': epoch_name,
        'task_name': task_name,
        'status': 'failed',
        'execution_time': 0,
        'output': '',
        'error': '',
        'artifacts': {}
    }

    try:
        agent_src_dir = base_dir / "epochs" / epoch_name / "agent-src"
        task_run_dir = base_dir / "epochs" / epoch_name / "runs" / task_name

        if not agent_src_dir.exists():
            raise FileNotFoundError(f"Agent source directory not found: {agent_src_dir}")

        # Build the Docker image
        build_proc = subprocess.run(
            ["docker", "build", "-t", image_tag, "."],
            cwd=agent_src_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute build timeout
        )
        
        if build_proc.returncode != 0:
            result['status'] = 'failed'
            result['error'] = f"Docker build failed:\nSTDOUT:\n{build_proc.stdout}\n\nSTDERR:\n{build_proc.stderr}"
            result['execution_time'] = time.time() - task_start_time
            return result

        # Run the Docker container with selective volume mounts (excluding tests folder)
        proc = subprocess.run([
            "docker", "run", "--rm",  # Automatically remove container when it exits
            "-t",  # Allocate a pseudo-TTY to fix prompt_toolkit warnings
            "--name", container_name,
            "--env-file", ".env",
            # Mount only specific folders that agent should have access to
            "-v", f"{task_run_dir}/input:/app/workspace/input",
            "-v", f"{task_run_dir}/output:/app/workspace/output",
            "-v", f"{task_run_dir}/expected-output:/app/workspace/expected-output",
            # Mount logs separately (agent should write logs to output folder)
            "-v", f"{task_run_dir}/output:/app/logs", 
            image_tag
        ], 
            cwd=agent_src_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        execution_time = time.time() - task_start_time
        result['execution_time'] = execution_time
        result['output'] = proc.stdout
        result['error'] = proc.stderr
        result['artifacts']['return_code'] = proc.returncode

        # Save full docker output for debugging and create log file
        result['docker_output'] = {
            'stdout': proc.stdout,
            'stderr': proc.stderr,
            'returncode': proc.returncode
        }
        
        # Save container logs to a file for inspection
        logs_file = task_run_dir / "container_logs.txt"
        with open(logs_file, 'w') as f:
            f.write(f"=== Container Execution Logs ===\n")
            f.write(f"Return Code: {proc.returncode}\n")
            f.write(f"Execution Time: {execution_time:.2f}s\n\n")
            f.write(f"=== STDOUT ===\n{proc.stdout}\n\n")
            f.write(f"=== STDERR ===\n{proc.stderr}\n")
        
        # The task is considered "completed" for validation purposes if it ran,
        # even if it exited with an error code, as long as it produced output.
        # This allows the validation step to score partially correct solutions.
        output_dir = task_run_dir / "output"
        if output_dir.exists() and any(output_dir.iterdir()):
             result['status'] = 'completed'
        else:
            result['status'] = 'failed'
            if proc.returncode != 0:
                result['error'] = f"Docker exited with code {proc.returncode} and produced no output files:\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"

    except subprocess.TimeoutExpired:
        result['status'] = 'failed'
        result['error'] = f"Task timed out after {timeout_seconds} seconds."
        result['execution_time'] = timeout_seconds
    except Exception:
        result['status'] = 'failed'
        result['error'] = traceback.format_exc()
        result['execution_time'] = time.time() - task_start_time
    finally:
        # Always clean up Docker image after execution
        try:
            # Remove the container if it still exists (in case --rm didn't work)
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True, timeout=30
            )
            # Remove the image to save disk space
            subprocess.run(
                ["docker", "rmi", "-f", image_tag],
                capture_output=True, timeout=30
            )
        except Exception:
            pass  # Don't fail the task if cleanup fails
        
    return result

def run_validation_task(args: Tuple[str, str, Path, int]) -> Dict[str, Any]:
    """
    Worker function to validate the output of a task.
    This replaces the old validation-worker.py.
    """
    epoch_name, task_name, base_dir, timeout_seconds = args
    task_start_time = time.time()
    
    result = {
        'epoch_name': epoch_name,
        'task_name': task_name,
        'status': 'failed',
        'execution_time': 0,
        'output': '',
        'error': '',
        'artifacts': {
            'compilation_score': 0,
            'test_score': 0,
        }
    }

    try:
        validation_dir = base_dir / "epochs" / epoch_name / "runs" / task_name
        
        if not validation_dir.exists():
            raise FileNotFoundError(f"Task run directory not found: {validation_dir}")

        # --- Step 1: Compilation Check ---
        output_dir = validation_dir / "output"
        py_files = list(output_dir.glob("*.py"))
        if not py_files:
            result['error'] = "No Python files found in output directory to validate."
            # This is a valid state, not an error in the validator itself.
            result['status'] = 'completed'
            return result

        compile_proc = subprocess.run(
            [sys.executable, "-m", "py_compile"] + [str(f) for f in py_files],
            capture_output=True, text=True, timeout=60
        )
        
        if compile_proc.returncode == 0:
            result['artifacts']['compilation_score'] = 1
        else:
            result['error'] += f"Compilation failed:\n{compile_proc.stderr}\n"

        # --- Step 2: Test Execution ---
        tests_dir = validation_dir / "tests"
        if tests_dir.exists() and list(tests_dir.glob("test_*.py")):
            # Create a temporary directory to run tests in isolation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                # Copy generated code and tests to the temp directory
                shutil.copytree(output_dir, temp_path / "output")
                shutil.copytree(tests_dir, temp_path / "tests")

                # Add the generated code directory to the Python path for the test run
                test_env = os.environ.copy()
                test_env['PYTHONPATH'] = str(temp_path / "output") + os.pathsep + test_env.get('PYTHONPATH', '')

                test_proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                    cwd=temp_path,
                    capture_output=True, text=True, timeout=timeout_seconds,
                    env=test_env
                )
                result['output'] = test_proc.stdout
                result['error'] += test_proc.stderr
                
                # Save test output to a file for debugging
                test_logs_file = validation_dir / "test_logs.txt"
                with open(test_logs_file, 'w') as f:
                    f.write(f"=== Test Execution Logs ===\n")
                    f.write(f"Return Code: {test_proc.returncode}\n\n")
                    f.write(f"=== STDOUT ===\n{test_proc.stdout}\n\n")
                    f.write(f"=== STDERR ===\n{test_proc.stderr}\n")

                if test_proc.returncode == 0:
                    result['artifacts']['test_score'] = 1
        else:
            result['error'] += "No tests found to run."

        result['status'] = 'completed'

    except subprocess.TimeoutExpired:
        result['status'] = 'failed'
        result['error'] = f"Validation timed out after {timeout_seconds} seconds."
    except Exception:
        result['status'] = 'failed'
        result['error'] = traceback.format_exc()
        
    result['execution_time'] = time.time() - task_start_time
    return result

# --- Main Evaluator Class ---

class EpochEvaluator:
    """Manages evaluation of an epoch against all default tasks"""
    
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.base_dir = Path(__file__).parent.parent
    
    def evaluate_epoch(self, epoch_name: str, generate_metrics: bool = True) -> Dict[str, Any]:
        """
        Evaluate an epoch against all default tasks.
        This script now manages its own parallel execution.
        """
        print(f"🔍 Starting evaluation of {epoch_name}")
        
        # Validate epoch exists
        epoch_dir = self.base_dir / "epochs" / epoch_name
        if not epoch_dir.exists():
            raise ValueError(f"Epoch directory not found: {epoch_dir}")
        
        # Setup tasks
        task_names = self._setup_tasks(epoch_name)
        if not task_names:
            raise ValueError("No tasks found to evaluate")
        
        print(f"📋 Found {len(task_names)} tasks for evaluation")
        
        # --- Phase 1: Run Task Evaluations in Parallel ---
        print("\n--- Running Task Evaluations ---")
        eval_tasks = [(epoch_name, task, self.base_dir, self.config.timeouts.task_execution_timeout) for task in task_names]
        evaluation_results = self._run_parallel_tasks(run_evaluation_task, eval_tasks, "Evaluation")

        # --- Phase 2: Run Validation in Parallel for Completed Tasks ---
        print("\n--- Running Validations ---")
        completed_tasks = [r['task_name'] for r in evaluation_results.values() if r['status'] == 'completed']
        if completed_tasks:
            validation_tasks = [(epoch_name, task, self.base_dir, self.config.timeouts.validation_timeout) for task in completed_tasks]
            validation_results = self._run_parallel_tasks(run_validation_task, validation_tasks, "Validation")
        else:
            print("No tasks completed successfully, skipping validation.")
            validation_results = {}

        # --- Phase 3: Generate Summary ---
        summary = self._generate_evaluation_summary(epoch_name, evaluation_results, validation_results, task_names)
        
        # Save the detailed summary that metrics collectors will use
        summary_file = self.base_dir / "epochs" / epoch_name / "evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n💾 Detailed evaluation summary saved to: {summary_file.relative_to(self.base_dir.parent)}")
        
        # Automatically generate metrics
        if generate_metrics:
            print("\n📊 Generating comprehensive metrics...")
            metrics_summary = self._generate_comprehensive_metrics(epoch_name)
            summary['metrics'] = metrics_summary
        else:
            print("\n📊 Skipping metrics generation (disabled)")
            summary['metrics'] = {'skipped': True, 'reason': 'Disabled by user'}
        
        return summary

    def _run_parallel_tasks(self, worker_func, tasks: List[Tuple], phase_name: str) -> Dict[str, Any]:
        """
        Runs a set of tasks in parallel using a multiprocessing Pool.
        """
        results = {}
        max_workers = self.config.parallelism.max_concurrent_jobs
        print(f"Starting {phase_name} phase with up to {max_workers} parallel processes.")

        with multiprocessing.Pool(processes=max_workers) as pool:
            iterator = pool.imap_unordered(worker_func, tasks)
            
            for i, result in enumerate(iterator, 1):
                task_name = result['task_name']
                results[task_name] = result
                
                # Live progress update
                status_icon = "✅" if result['status'] == 'completed' else "❌"
                print(f"[{i}/{len(tasks)}] {status_icon} {phase_name} for {task_name} finished with status: {result['status']}")
                
                if result['status'] == 'failed':
                    error_snippet = result.get('error', 'No error details.').strip().replace('\n', ' ')
                    print(f"  ERROR for {task_name}: {error_snippet[:300]}...")
                
                # Save detailed docker output for debugging (for both success and failure)
                if 'docker_output' in result:
                    task_run_dir = self.base_dir / "epochs" / result['epoch_name'] / "runs" / task_name
                    task_run_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save stdout and stderr as separate text files
                    stdout_file = task_run_dir / f"docker_stdout_{phase_name.lower().replace(' ', '_')}.txt"
                    stderr_file = task_run_dir / f"docker_stderr_{phase_name.lower().replace(' ', '_')}.txt"
                    
                    with open(stdout_file, 'w') as f:
                        f.write(result['docker_output']['stdout'])
                    with open(stderr_file, 'w') as f:
                        f.write(result['docker_output']['stderr'])

        if len(results) != len(tasks):
            print(f"⚠️ Warning: Expected {len(tasks)} results, but only received {len(results)}.")

        return results

    def _setup_tasks(self, epoch_name: str) -> List[str]:
        """Copy default workspaces to epoch runs directory."""
        print("📁 Setting up tasks...")
        default_workspaces = self.base_dir / "default-workspaces"
        epoch_runs = self.base_dir / "epochs" / epoch_name / "runs"
        
        if not default_workspaces.exists():
            raise ValueError(f"Default workspaces not found: {default_workspaces}")
        
        epoch_runs.mkdir(parents=True, exist_ok=True)
        
        task_dirs = sorted([d for d in default_workspaces.iterdir() if d.is_dir()])
        if not task_dirs:
            raise ValueError("No task directories found in default workspaces")
        
        task_names = []
        for task_dir in task_dirs:
            task_name = task_dir.name
            target_dir = epoch_runs / task_name
            
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            shutil.copytree(task_dir, target_dir)
            (target_dir / "output").mkdir(exist_ok=True)
            task_names.append(task_name)
        
        print(f"✅ Set up {len(task_names)} tasks: {', '.join(task_names)}")
        return task_names

    def _generate_evaluation_summary(self, epoch_name: str, 
                                   eval_results: Dict[str, Any],
                                   val_results: Dict[str, Any],
                                   task_names: List[str]) -> Dict[str, Any]:
        """Generate evaluation summary from task results."""
        print("\n📊 Generating evaluation summary...")
        
        summary = {
            'epoch': epoch_name,
            'total_tasks': len(eval_results),
            'successful_tasks': 0,
            'failed_tasks': 0,
            'validated_tasks': len(val_results),
            'task_results': {},
            'overall_score': 0,
            'max_possible_score': len(eval_results) * 3,  # 1 completion + 1 compilation + 1 tests
            'success_rate': 0.0
        }
        
        for task_name in task_names:
            result = eval_results[task_name]
            task_result = {
                'status': result['status'],
                'execution_time': result.get('execution_time', 0),
                'task_completion_score': 1 if result['status'] == 'completed' else 0,
                'compilation_score': 0,
                'test_score': 0,
                'total_score': 0,
                'validation_status': 'not_run',
                'error': result.get('error')
            }

            if result['status'] == 'completed':
                summary['successful_tasks'] += 1
                if task_name in val_results:
                    val_result = val_results[task_name]
                    task_result['validation_status'] = val_result['status']
                    if val_result['status'] == 'completed':
                        task_result['compilation_score'] = val_result['artifacts'].get('compilation_score', 0)
                        task_result['test_score'] = val_result['artifacts'].get('test_score', 0)
                    if val_result.get('error'):
                        task_result['error'] = (task_result.get('error') or "") + "\nValidation Error:\n" + val_result['error']
            else:
                summary['failed_tasks'] += 1

            task_result['total_score'] = (task_result['task_completion_score'] + 
                                         task_result['compilation_score'] + 
                                         task_result['test_score'])
            summary['overall_score'] += task_result['total_score']
            summary['task_results'][task_name] = task_result

        if summary['max_possible_score'] > 0:
            summary['success_rate'] = (summary['overall_score'] / summary['max_possible_score']) * 100
        
        print(f"📈 Evaluation Summary for {epoch_name}:")
        print(f"   Tasks: {summary['successful_tasks']}/{summary['total_tasks']} completed")
        print(f"   Overall Score: {summary['overall_score']}/{summary['max_possible_score']} ({summary['success_rate']:.1f}%)")
        
        return summary

    def _generate_comprehensive_metrics(self, epoch_name: str) -> Dict[str, Any]:
        """Generate comprehensive metrics using the metrics system."""
        try:
            sys.path.insert(0, str(self.base_dir / "evaluation" / "metrics-collectors"))
            from score_calculator import ScoreCalculator
            from report_generator import ReportGenerator
            from epoch_analyzer import EpochAnalyzer
            
            calculator = ScoreCalculator()
            report_generator = ReportGenerator()
            analyzer = EpochAnalyzer()
            
            print("   📊 Calculating epoch scores...")
            epoch_score = calculator.calculate_epoch_score(epoch_name)
            
            print("   📋 Generating detailed reports...")
            report_files = report_generator.generate_epoch_report(epoch_name)

            print("   🔍 Analyzing epoch performance...")
            analysis = analyzer.analyze_epoch(epoch_name)
            
            metrics_summary = {
                'score_summary': json.loads(json.dumps(epoch_score, default=lambda o: o.isoformat() if isinstance(o, datetime) else o.__dict__)),
                'reports_generated': report_files,
                'analysis': analysis
            }
            print("   ✅ Metrics generation complete!")
            return metrics_summary
            
        except Exception as e:
            print(f"   ❌ Metrics generation failed: {traceback.format_exc()}")
            return {'error': str(e)}

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Evaluate an epoch against all default tasks")
    parser.add_argument("--epoch", required=True, help="Epoch name to evaluate (e.g., epoch-001)")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--no-metrics", action="store_true", help="Skip automatic metrics generation")
    
    args = parser.parse_args()
    
    try:
        evaluator = EpochEvaluator(args.config)
        summary = evaluator.evaluate_epoch(args.epoch, generate_metrics=not args.no_metrics)
        
        print(f"\n🎉 Evaluation of {args.epoch} completed!")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
