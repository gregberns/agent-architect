#!/usr/bin/env python3
"""
Report Generator - creates JSON and CSV reports for epoch performance analysis
"""

import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from score_calculator import ScoreCalculator, EpochScore, TaskScore

class ReportGenerator:
    """Generates performance reports in various formats"""
    
    def __init__(self, config_path: str = None):
        self.calculator = ScoreCalculator(config_path)
        self.base_dir = Path(__file__).parent.parent.parent
    
    def generate_epoch_report(self, epoch: str, output_dir: str = None, 
                            formats: List[str] = None) -> Dict[str, str]:
        """
        Generate comprehensive report for an epoch
        
        Args:
            epoch: Epoch name (e.g., 'epoch-001')
            output_dir: Directory to save reports (default: epoch metrics dir)
            formats: List of formats ['json', 'csv'] (default: both)
            
        Returns:
            Dictionary mapping format to output file path
        """
        if formats is None:
            formats = ['json', 'csv']
        
        if output_dir is None:
            output_dir = self.base_dir / "epochs" / epoch / "metrics"
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate epoch score
        epoch_score = self.calculator.calculate_epoch_score(epoch)
        
        # Generate reports
        output_files = {}
        
        if 'json' in formats:
            json_file = self._generate_json_report(epoch_score, output_dir)
            output_files['json'] = str(json_file)
        
        if 'csv' in formats:
            csv_file = self._generate_csv_report(epoch_score, output_dir)
            output_files['csv'] = str(csv_file)
        
        return output_files
    
    def generate_comparison_report(self, epochs: List[str], output_dir: str = None) -> Dict[str, str]:
        """
        Generate comparison report across multiple epochs
        
        Args:
            epochs: List of epoch names to compare
            output_dir: Directory to save reports (default: base metrics dir)
            
        Returns:
            Dictionary mapping format to output file path
        """
        if output_dir is None:
            output_dir = self.base_dir / "evaluation" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate scores for all epochs
        epoch_scores = {}
        for epoch in epochs:
            try:
                epoch_scores[epoch] = self.calculator.calculate_epoch_score(epoch)
            except Exception as e:
                print(f"Warning: Could not calculate score for {epoch}: {e}")
        
        if not epoch_scores:
            raise ValueError("No valid epoch scores found")
        
        # Generate comparison reports
        output_files = {}
        
        json_file = self._generate_comparison_json(epoch_scores, output_dir)
        output_files['json'] = str(json_file)
        
        csv_file = self._generate_comparison_csv(epoch_scores, output_dir)
        output_files['csv'] = str(csv_file)
        
        return output_files
    
    def _generate_json_report(self, epoch_score: EpochScore, output_dir: Path) -> Path:
        """Generate detailed JSON report for a single epoch"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{epoch_score.epoch}_score_report_{timestamp}.json"
        output_file = output_dir / filename
        
        # Convert epoch score to detailed dictionary
        report = json.loads(json.dumps(epoch_score, default=lambda o: o.isoformat() if isinstance(o, datetime) else o.__dict__))
        
        # Write JSON report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Generated JSON report: {output_file}")
        return output_file
    
    def _generate_csv_report(self, epoch_score: EpochScore, output_dir: Path) -> Path:
        """Generate CSV report for a single epoch (task-level data)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{epoch_score.epoch}_tasks_{timestamp}.csv"
        output_file = output_dir / filename
        
        # Define CSV columns
        fieldnames = [
            'task_name', 'status', 'total_score', 'max_possible_score', 'success_rate',
            'task_completion_score', 'compilation_score', 'test_score', 'execution_time',
            'error_message'
        ]
        
        # Write CSV report
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for task_name, task_score in epoch_score.task_scores.items():
                writer.writerow({
                    'task_name': task_name,
                    'status': task_score.status,
                    'total_score': task_score.total_score,
                    'max_possible_score': task_score.max_possible_score,
                    'success_rate': round(task_score.success_rate, 2),
                    'task_completion_score': task_score.task_completion_score,
                    'compilation_score': task_score.compilation_score,
                    'test_score': task_score.test_score,
                    'execution_time': round(task_score.execution_time, 3),
                    'error_message': task_score.error_message or ''
                })
        
        print(f"Generated CSV report: {output_file}")
        return output_file
    
    def _generate_comparison_json(self, epoch_scores: Dict[str, EpochScore], 
                                 output_dir: Path) -> Path:
        """Generate JSON comparison report across epochs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"epoch_comparison_{timestamp}.json"
        output_file = output_dir / filename
        
        # Build comparison report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'compared_epochs': list(epoch_scores.keys()),
                'report_version': '1.1'
            },
            'summary': {},
            'task_comparison': {}
        }
        
        # Epoch-level summary
        for epoch, score in epoch_scores.items():
            report['summary'][epoch] = {
                'total_score': score.total_score,
                'max_possible_score': score.max_possible_score,
                'success_rate': round(score.success_rate, 2),
                'completed_tasks': score.completed_tasks,
                'total_tasks': score.total_tasks,
                'compilation_success_rate': round(score.compilation_success_rate, 2),
                'test_success_rate': round(score.test_success_rate, 2)
            }
        
        # Task-level comparison
        all_tasks = set()
        for score in epoch_scores.values():
            all_tasks.update(score.task_scores.keys())
        
        for task in sorted(all_tasks):
            report['task_comparison'][task] = {}
            for epoch, score in epoch_scores.items():
                if task in score.task_scores:
                    task_score = score.task_scores[task]
                    report['task_comparison'][task][epoch] = {
                        'total_score': task_score.total_score,
                        'success_rate': round(task_score.success_rate, 2),
                        'status': task_score.status
                    }
                else:
                    report['task_comparison'][task][epoch] = {
                        'total_score': 0,
                        'success_rate': 0.0,
                        'status': 'not_run'
                    }
        
        # Write JSON report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Generated comparison JSON report: {output_file}")
        return output_file
    
    def _generate_comparison_csv(self, epoch_scores: Dict[str, EpochScore], 
                                output_dir: Path) -> Path:
        """Generate CSV comparison report across epochs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"epoch_comparison_{timestamp}.csv"
        output_file = output_dir / filename
        
        # Define CSV columns
        fieldnames = [
            'epoch', 'total_score', 'max_possible_score', 'success_rate',
            'completed_tasks', 'total_tasks', 'compilation_success_rate',
            'test_success_rate', 'failed_tasks'
        ]
        
        # Write CSV report
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for epoch in sorted(epoch_scores.keys()):
                score = epoch_scores[epoch]
                writer.writerow({
                    'epoch': epoch,
                    'total_score': score.total_score,
                    'max_possible_score': score.max_possible_score,
                    'success_rate': round(score.success_rate, 2),
                    'completed_tasks': score.completed_tasks,
                    'total_tasks': score.total_tasks,
                    'compilation_success_rate': round(score.compilation_success_rate, 2),
                    'test_success_rate': round(score.test_success_rate, 2),
                    'failed_tasks': score.failed_tasks
                })
        
        print(f"Generated comparison CSV report: {output_file}")
        return output_file
    
    def get_available_epochs(self) -> List[str]:
        """Get list of available epochs for reporting"""
        epochs_dir = self.base_dir / "epochs"
        if not epochs_dir.exists():
            return []
        
        return sorted([d.name for d in epochs_dir.iterdir() 
                      if d.is_dir() and d.name.startswith('epoch-')])

def main():
    """CLI interface for report generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate performance reports")
    report_group = parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--epoch", help="Single epoch to report on")
    report_group.add_argument("--compare", nargs='+', help="Multiple epochs to compare")
    report_group.add_argument("--list-epochs", action="store_true", help="List available epochs")
    parser.add_argument("--output-dir", help="Output directory for reports")
    parser.add_argument("--formats", nargs='+', choices=['json', 'csv'], 
                       default=['json', 'csv'], help="Output formats")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.list_epochs:
        epochs = generator.get_available_epochs()
        print("Available epochs:")
        for epoch in epochs:
            print(f"  {epoch}")
        return
    
    if args.epoch:
        # Single epoch report
        try:
            output_files = generator.generate_epoch_report(
                args.epoch, args.output_dir, args.formats
            )
            print(f"\nReports generated for {args.epoch}:")
            for format_type, file_path in output_files.items():
                print(f"  {format_type.upper()}: {file_path}")
        except Exception as e:
            print(f"Error generating report for {args.epoch}: {e}")
            sys.exit(1)
    
    elif args.compare:
        # Comparison report
        try:
            output_files = generator.generate_comparison_report(
                args.compare, args.output_dir
            )
            print(f"\nComparison reports generated for epochs: {', '.join(args.compare)}")
            for format_type, file_path in output_files.items():
                print(f"  {format_type.upper()}: {file_path}")
        except Exception as e:
            print(f"Error generating comparison report: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
