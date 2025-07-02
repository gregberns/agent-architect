#!/usr/bin/env python3
"""
Agent Evolution Script

Takes a validated agent from a parent epoch, copies it to new epoch(s), 
provides it with validation logs from its performance, and runs an evolution 
process where the agent can improve itself.

Usage:
    python -m orchestrator.evolve_epoch --parent-epoch epoch-000 [--num-copies 1] [--config config.json]
"""

import argparse
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class EpochEvolver:
    """Manages the agent evolution process"""
    
    def __init__(self, base_dir: Path, config: Optional[Dict[str, Any]] = None):
        self.base_dir = base_dir
        self.config = config or {}
        
        # Default configuration values
        self.evolution_timeout = self.config.get('evolution_timeout_seconds', 600)  # 10 minutes
        self.container_memory = self.config.get('evolution_container_memory', '2g')
        self.log_level = self.config.get('evolution_log_level', 'INFO')
    
    def evolve_agent(self, parent_epoch: str, num_copies: int = 1) -> List[str]:
        """
        Main evolution process
        
        Args:
            parent_epoch: Source epoch name (e.g., 'epoch-000')
            num_copies: Number of evolution epochs to create
            
        Returns:
            List of created epoch names
        """
        print(f"🧬 Starting agent evolution from {parent_epoch}")
        
        # Phase 1: Setup and Validation
        self._validate_parent_epoch(parent_epoch)
        new_epoch_names = self._generate_new_epoch_names(num_copies)
        
        print(f"📁 Creating {num_copies} evolution epoch(s): {', '.join(new_epoch_names)}")
        
        created_epochs = []
        for epoch_name in new_epoch_names:
            try:
                self._setup_evolution_epoch(parent_epoch, epoch_name)
                created_epochs.append(epoch_name)
                print(f"✅ Set up evolution epoch: {epoch_name}")
            except Exception as e:
                print(f"❌ Failed to set up {epoch_name}: {e}")
                # Continue with other epochs
                continue
        
        # Phase 2: Evolution Process
        evolution_results = []
        for epoch_name in created_epochs:
            try:
                result = self._run_evolution_process(epoch_name)
                evolution_results.append(result)
                if result['success']:
                    print(f"🎉 Evolution completed successfully for {epoch_name}")
                else:
                    print(f"⚠️ Evolution failed for {epoch_name}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Evolution process failed for {epoch_name}: {e}")
                evolution_results.append({'epoch': epoch_name, 'success': False, 'error': str(e)})
        
        print(f"\n📊 Evolution Summary:")
        successful = [r for r in evolution_results if r['success']]
        print(f"  Successful: {len(successful)}/{len(evolution_results)}")
        print(f"  Created epochs: {[r['epoch'] for r in successful]}")
        
        return [r['epoch'] for r in successful]
    
    def _validate_parent_epoch(self, parent_epoch: str) -> None:
        """Validate that parent epoch exists and has required validation data"""
        parent_dir = self.base_dir / "epochs" / parent_epoch / "validation"
        
        if not parent_dir.exists():
            raise ValueError(f"Parent epoch validation directory not found: {parent_dir}")
        
        # Check for evaluation summary
        summary_file = parent_dir / "evaluation_summary.json"
        if not summary_file.exists():
            raise ValueError(f"Parent epoch missing evaluation_summary.json: {summary_file}")
        
        # Check for metrics directory
        metrics_dir = parent_dir / "metrics"
        if not metrics_dir.exists():
            raise ValueError(f"Parent epoch missing metrics directory: {metrics_dir}")
        
        # Check for runs directory
        runs_dir = parent_dir / "runs"
        if not runs_dir.exists():
            raise ValueError(f"Parent epoch missing runs directory: {runs_dir}")
        
        print(f"✅ Parent epoch {parent_epoch} validation passed")
    
    def _generate_new_epoch_names(self, num_copies: int) -> List[str]:
        """Generate new epoch names by finding highest existing epoch number"""
        epochs_dir = self.base_dir / "epochs"
        
        if not epochs_dir.exists():
            raise ValueError(f"Epochs directory not found: {epochs_dir}")
        
        # Find all existing epoch directories
        existing_epochs = []
        epoch_pattern = re.compile(r'^epoch-(\d+)$')
        
        for item in epochs_dir.iterdir():
            if item.is_dir():
                match = epoch_pattern.match(item.name)
                if match:
                    epoch_num = int(match.group(1))
                    existing_epochs.append(epoch_num)
        
        if not existing_epochs:
            raise ValueError("No existing epochs found")
        
        # Start from highest existing epoch + 1
        highest_epoch = max(existing_epochs)
        next_epoch_num = highest_epoch + 1
        
        # Generate new epoch names
        new_epoch_names = []
        for i in range(num_copies):
            epoch_name = f"epoch-{next_epoch_num + i:03d}"
            
            # Double-check that epoch doesn't exist
            epoch_dir = epochs_dir / epoch_name
            if epoch_dir.exists():
                raise ValueError(f"Epoch {epoch_name} already exists - cannot overwrite")
            
            new_epoch_names.append(epoch_name)
        
        print(f"📋 Next available epochs: {new_epoch_names}")
        return new_epoch_names
    
    def _setup_evolution_epoch(self, parent_epoch: str, new_epoch: str) -> None:
        """Set up directory structure and files for evolution epoch"""
        parent_dir = self.base_dir / "epochs" / parent_epoch / "validation"
        new_epoch_dir = self.base_dir / "epochs" / new_epoch
        evolution_dir = new_epoch_dir / "evolution"
        
        # Create directory structure
        evolution_dir.mkdir(parents=True, exist_ok=True)
        (evolution_dir / "agent-src").mkdir(exist_ok=True)
        (evolution_dir / "input").mkdir(exist_ok=True)
        (evolution_dir / "input" / "agent-src").mkdir(exist_ok=True)
        (evolution_dir / "input" / "validation-logs").mkdir(exist_ok=True)
        (evolution_dir / "input" / "validation-logs" / "task-results").mkdir(exist_ok=True)
        (evolution_dir / "output").mkdir(exist_ok=True)
        
        # Copy agent source code to both locations
        parent_agent_src = parent_dir / "agent-src"
        
        # Copy to evolution/agent-src (agent to be evolved)
        if parent_agent_src.exists():
            shutil.copytree(parent_agent_src, evolution_dir / "agent-src", dirs_exist_ok=True)
        else:
            raise ValueError(f"Parent agent source not found: {parent_agent_src}")
        
        # Copy to evolution/input/agent-src (reference copy)
        shutil.copytree(parent_agent_src, evolution_dir / "input" / "agent-src", dirs_exist_ok=True)
        
        # Collect and organize validation logs
        self._collect_validation_logs(parent_dir, evolution_dir / "input" / "validation-logs")
        
        # Create parent tracking file
        self._create_parent_tracking_file(parent_epoch, new_epoch, parent_dir)
        
        print(f"📂 Evolution directory structure created for {new_epoch}")
    
    def _collect_validation_logs(self, parent_validation_dir: Path, logs_dir: Path) -> None:
        """Collect and organize validation logs from parent epoch"""
        
        # Find latest metrics CSV file
        metrics_dir = parent_validation_dir / "metrics"
        csv_files = list(metrics_dir.glob("*.csv"))
        
        if csv_files:
            # Sort by modification time and get the latest
            latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
            shutil.copy2(latest_csv, logs_dir / "metrics.csv")
            print(f"📊 Copied latest metrics: {latest_csv.name}")
        else:
            print("⚠️ No CSV metrics files found in parent epoch")
        
        # Collect task results
        runs_dir = parent_validation_dir / "runs"
        task_results_dir = logs_dir / "task-results"
        
        if runs_dir.exists():
            for task_dir in runs_dir.iterdir():
                if task_dir.is_dir():
                    task_name = task_dir.name
                    task_log_dir = task_results_dir / task_name
                    task_log_dir.mkdir(exist_ok=True)
                    
                    # Copy test_logs.txt
                    test_logs = task_dir / "test_logs.txt"
                    if test_logs.exists():
                        shutil.copy2(test_logs, task_log_dir / "test_logs.txt")
                    
                    # Copy container_logs.txt
                    container_logs = task_dir / "container_logs.txt"
                    if container_logs.exists():
                        shutil.copy2(container_logs, task_log_dir / "container_logs.txt")
                    
                    # Copy all output files
                    output_dir = task_dir / "output"
                    if output_dir.exists():
                        task_output_dir = task_log_dir / "output"
                        shutil.copytree(output_dir, task_output_dir, dirs_exist_ok=True)
                    
                    print(f"📝 Collected logs for task: {task_name}")
    
    def _create_parent_tracking_file(self, parent_epoch: str, new_epoch: str, parent_validation_dir: Path) -> None:
        """Create parent tracking file with lineage information"""
        
        # Load parent evaluation summary for score data
        summary_file = parent_validation_dir / "evaluation_summary.json"
        parent_score = 0.0
        parent_success_rate = "0%"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    parent_score = summary.get('total_score', 0.0)
                    
                    # Calculate success rate
                    total_tasks = len(summary.get('task_results', {}))
                    successful_tasks = sum(1 for result in summary.get('task_results', {}).values() 
                                         if result.get('evaluation_success', False) and 
                                            result.get('validation_success', False))
                    parent_success_rate = f"{(successful_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
            except Exception as e:
                print(f"⚠️ Could not load parent summary data: {e}")
        
        parent_info = {
            "parent_epoch": parent_epoch,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evolution_generation": 1,  # TODO: Could track deeper lineage
            "parent_score": parent_score,
            "parent_success_rate": parent_success_rate
        }
        
        parent_file = self.base_dir / "epochs" / new_epoch / "parent.json"
        with open(parent_file, 'w') as f:
            json.dump(parent_info, f, indent=2)
        
        print(f"📋 Parent tracking file created: {parent_file}")
    
    def _run_evolution_process(self, epoch_name: str) -> Dict[str, Any]:
        """Run the evolution process for a specific epoch"""
        evolution_dir = self.base_dir / "epochs" / epoch_name / "evolution"
        
        print(f"\n🧬 Starting evolution process for {epoch_name}")
        
        # Pre-evolution validation: Check for TASK.md
        task_file = evolution_dir / "input" / "agent-src" / "TASK.md"
        if not task_file.exists():
            error_msg = f"""❌ ERROR: Missing required TASK.md file

The evolution process requires a TASK.md file that describes what the agent should do.
Expected location: {task_file}

Please create this file with instructions for the agent's evolution task before continuing."""
            print(error_msg)
            return {
                'epoch': epoch_name,
                'success': False,
                'error': 'Missing TASK.md file',
                'details': error_msg
            }
        
        # Build Docker image
        build_result = self._build_evolution_image(epoch_name, evolution_dir)
        if not build_result['success']:
            return {
                'epoch': epoch_name,
                'success': False,
                'error': 'Docker build failed',
                'details': build_result.get('error', 'Unknown build error')
            }
        
        # Run evolution container
        container_result = self._run_evolution_container(epoch_name, evolution_dir, build_result['image_tag'])
        
        return {
            'epoch': epoch_name,
            'success': container_result['success'],
            'error': container_result.get('error'),
            'details': container_result.get('details'),
            'container_logs': container_result.get('logs_file')
        }
    
    def _build_evolution_image(self, epoch_name: str, evolution_dir: Path) -> Dict[str, Any]:
        """Build Docker image for evolution"""
        image_tag = f"agent-evolution-{epoch_name}"
        agent_src_dir = evolution_dir / "agent-src"
        
        print(f"🐳 Building Docker image: {image_tag}")
        
        try:
            build_proc = subprocess.run(
                ["docker", "build", "-t", image_tag, "."],
                cwd=agent_src_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute build timeout
            )
            
            if build_proc.returncode == 0:
                print(f"✅ Docker image built successfully: {image_tag}")
                return {'success': True, 'image_tag': image_tag}
            else:
                error_msg = f"Docker build failed with code {build_proc.returncode}\nSTDOUT:\n{build_proc.stdout}\nSTDERR:\n{build_proc.stderr}"
                print(f"❌ Docker build failed: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except subprocess.TimeoutExpired:
            error_msg = "Docker build timed out after 5 minutes"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Docker build error: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _run_evolution_container(self, epoch_name: str, evolution_dir: Path, image_tag: str) -> Dict[str, Any]:
        """Run evolution container with real-time log streaming"""
        container_name = f"evolution-{epoch_name}-{int(time.time())}"
        
        print(f"🚀 Starting evolution container: {container_name}")
        print(f"⏱️ Timeout: {self.evolution_timeout} seconds")
        
        # Prepare log file (truncate/overwrite existing file)
        log_file = evolution_dir / "evolution_container_logs.txt"
        
        try:
            # Prepare Docker command (match evaluate_epoch.py pattern exactly)
            docker_cmd = [
                "docker", "run", "--rm", "-t", "--name", container_name,
                "--env-file", ".env",  # Match evaluate_epoch.py exactly
                "-v", f"{evolution_dir}/input:/app/workspace/input:ro",  # Read-only
                "-v", f"{evolution_dir}/output:/app/workspace/output",   # Read-write
                "-v", f"{evolution_dir}/output:/app/logs",               # For debug logs
                image_tag
            ]
            
            # Start container in background
            proc = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=self.base_dir)
            
            # Stream logs to file in real-time (truncate/overwrite existing file)
            with open(log_file, 'w') as f:  # 'w' mode truncates existing file
                def stream_logs():
                    try:
                        for line in proc.stdout:
                            f.write(line)
                            f.flush()  # Ensure immediate write
                            print(f"[{epoch_name}] {line.strip()}")  # Also show on console
                    except Exception as e:
                        print(f"⚠️ Log streaming error: {e}")
                
                log_thread = threading.Thread(target=stream_logs)
                log_thread.daemon = True
                log_thread.start()
                
                # Wait with timeout
                try:
                    exit_code = proc.wait(timeout=self.evolution_timeout)
                    log_thread.join(timeout=5)  # Give thread time to finish
                    
                    if exit_code == 0:
                        print(f"✅ Evolution container completed successfully")
                        return {'success': True, 'logs_file': str(log_file)}
                    else:
                        error_msg = f"Container exited with code {exit_code}"
                        print(f"❌ {error_msg}")
                        return {'success': False, 'error': error_msg, 'logs_file': str(log_file)}
                        
                except subprocess.TimeoutExpired:
                    print(f"⏰ Evolution timeout after {self.evolution_timeout} seconds")
                    proc.kill()
                    log_thread.join(timeout=5)
                    return {
                        'success': False, 
                        'error': f'Timeout after {self.evolution_timeout} seconds',
                        'logs_file': str(log_file)
                    }
                
        except Exception as e:
            error_msg = f"Container execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg, 'logs_file': str(log_file)}


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file if provided"""
    if not config_path:
        return {}
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise ValueError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Evolve agent from parent epoch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m orchestrator.evolve_epoch --parent-epoch epoch-000
  python -m orchestrator.evolve_epoch --parent-epoch epoch-000 --num-copies 3
  python -m orchestrator.evolve_epoch --parent-epoch epoch-002 --config evolution_config.json
        """
    )
    
    parser.add_argument(
        "--parent-epoch",
        required=True,
        help="Parent epoch to evolve from (e.g., epoch-000)"
    )
    
    parser.add_argument(
        "--num-copies", 
        type=int, 
        default=1,
        help="Number of evolution epochs to create (default: 1)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Initialize evolver
        base_dir = Path(__file__).parent.parent
        evolver = EpochEvolver(base_dir, config)
        
        # Run evolution
        created_epochs = evolver.evolve_agent(args.parent_epoch, args.num_copies)
        
        if created_epochs:
            print(f"\n🎉 Evolution completed successfully!")
            print(f"Created epochs: {', '.join(created_epochs)}")
            print(f"\nNext steps:")
            print(f"1. Review evolution results in each epoch's evolution/output/ directory")
            print(f"2. Run validation: python -m orchestrator.evaluate_epoch --epoch [new-epoch]")
        else:
            print(f"\n❌ No evolution epochs were created successfully")
            exit(1)
            
    except Exception as e:
        print(f"❌ Evolution failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()