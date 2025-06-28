#!/usr/bin/env python3
"""
Metrics CLI - unified command-line interface for all metrics collection tools
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from score_calculator import ScoreCalculator
from report_generator import ReportGenerator
from epoch_analyzer import EpochAnalyzer

def cmd_score(args):
    """Handle score calculation commands"""
    calculator = ScoreCalculator(args.config)
    
    try:
        if args.task:
            # Single task score
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
            # Epoch score
            epoch_score = calculator.calculate_epoch_score(args.epoch)
            print(f"Epoch Score for {args.epoch}:")
            print(f"  Total Score: {epoch_score.total_score}/{epoch_score.max_possible_score} ({epoch_score.success_rate:.1f}%)")
            print(f"  Tasks: {epoch_score.completed_tasks}/{epoch_score.total_tasks} completed")
            print(f"  Compilation Success: {epoch_score.compilation_success_rate:.1f}%")
            print(f"  Test Success: {epoch_score.test_success_rate:.1f}%")
            
            if args.verbose:
                print(f"\nTask Breakdown:")
                for task_name, task_score in epoch_score.task_scores.items():
                    status_icon = "✅" if task_score.status == "completed" else "❌"
                    print(f"  {status_icon} {task_name}: {task_score.total_score}/3 ({task_score.status})")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please run an evaluation for this epoch first.")
        sys.exit(1)

def cmd_report(args):
    """Handle report generation commands"""
    generator = ReportGenerator(args.config)
    
    if args.list_epochs:
        epochs = generator.get_available_epochs()
        print("Available epochs:")
        for epoch in epochs:
            print(f"  {epoch}")
        return
    
    if args.compare:
        # Comparison report
        try:
            output_files = generator.generate_comparison_report(
                args.compare, args.output_dir
            )
            print(f"Comparison reports generated for epochs: {', '.join(args.compare)}")
            for format_type, file_path in output_files.items():
                print(f"  {format_type.upper()}: {file_path}")
        except Exception as e:
            print(f"Error generating comparison report: {e}")
            sys.exit(1)
    
    elif args.epoch:
        # Single epoch report
        try:
            output_files = generator.generate_epoch_report(
                args.epoch, args.output_dir, args.formats
            )
            print(f"Reports generated for {args.epoch}:")
            for format_type, file_path in output_files.items():
                print(f"  {format_type.upper()}: {file_path}")
        except Exception as e:
            print(f"Error generating report for {args.epoch}: {e}")
            sys.exit(1)
    
    else:
        # All available epochs
        epochs = generator.get_available_epochs()
        if not epochs:
            print("No epochs found to report on")
            return
        
        print(f"Generating reports for all available epochs: {', '.join(epochs)}")
        for epoch in epochs:
            try:
                output_files = generator.generate_epoch_report(
                    epoch, args.output_dir, args.formats
                )
                print(f"  ✅ {epoch}: {len(output_files)} reports generated")
            except Exception as e:
                print(f"  ❌ {epoch}: {e}")

def cmd_analyze(args):
    """Handle analysis commands"""
    analyzer = EpochAnalyzer(args.config)
    
    try:
        results = {}
        
        if not args.tasks_only and not args.patterns_only:
            # Trend analysis
            trends = analyzer.analyze_trends(args.epochs)
            results['trends'] = {name: {
                'metric_name': trend.metric_name,
                'trend_direction': trend.trend_direction,
                'change_percentage': round(trend.change_percentage, 2),
                'best_epoch': trend.best_epoch,
                'worst_epoch': trend.worst_epoch,
                'values': trend.values
            } for name, trend in trends.items()}
            
            if not args.trends_only:
                print("📈 Trend Analysis:")
                for name, trend in trends.items():
                    direction_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(trend.trend_direction, "❓")
                    print(f"  {direction_icon} {trend.metric_name}: {trend.change_percentage:+.1f}% ({trend.trend_direction})")
        
        if not args.trends_only and not args.patterns_only:
            # Task progression analysis
            task_progressions = analyzer.analyze_task_progression(args.epochs)
            results['task_progressions'] = {name: {
                'best_score': prog.best_score,
                'best_epoch': prog.best_epoch,
                'consistency_score': round(prog.consistency_score, 2),
                'epoch_scores': prog.epoch_scores
            } for name, prog in task_progressions.items()}
            
            if not args.tasks_only:
                print(f"\n📋 Task Progression (Top 5 by consistency):")
                sorted_tasks = sorted(task_progressions.items(), key=lambda x: x[1].consistency_score, reverse=True)
                for task_name, prog in sorted_tasks[:5]:
                    print(f"  {task_name}: {prog.consistency_score:.1%} consistency, best: {prog.best_score}/3 ({prog.best_epoch})")
        
        if not args.trends_only and not args.tasks_only:
            # Performance patterns
            patterns = analyzer.find_performance_patterns(args.epochs)
            results['patterns'] = patterns
            
            if not args.patterns_only:
                print(f"\n🔍 Performance Patterns:")
                print(f"  Best epoch: {patterns['performance_summary']['best_performing_epoch']}")
                print(f"  Metrics trending up: {patterns['performance_summary']['trending_upward']}")
                print(f"  Metrics trending down: {patterns['performance_summary']['trending_downward']}")
                
                if patterns['recommendations']:
                    print(f"\n💡 Recommendations:")
                    for rec in patterns['recommendations']:
                        print(f"  • {rec}")
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📁 Analysis saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Metrics Collection System - unified interface for evaluation metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s score --epoch epoch-001
  %(prog)s score --epoch epoch-001 --task task-001
  
  %(prog)s report --epoch epoch-001
  %(prog)s report --compare epoch-001 epoch-002
  %(prog)s report --list-epochs
  
  %(prog)s analyze --epochs epoch-001 epoch-002 epoch-003
  %(prog)s analyze --epochs epoch-001 epoch-002 --trends-only
        """
    )
    
    # Global options
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)
    
    # Score command
    score_parser = subparsers.add_parser('score', help='Calculate task and epoch scores')
    score_parser.add_argument("--epoch", required=True, help="Epoch name (e.g., epoch-001)")
    score_parser.add_argument("--task", help="Specific task name (optional)")
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate performance reports')
    report_group = report_parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--epoch", help="Single epoch to report on")
    report_group.add_argument("--compare", nargs='+', help="Multiple epochs to compare")
    report_group.add_argument("--list-epochs", action="store_true", help="List available epochs")
    report_parser.add_argument("--output-dir", help="Output directory for reports")
    report_parser.add_argument("--formats", nargs='+', choices=['json', 'csv'], 
                              default=['json', 'csv'], help="Output formats")
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze trends and patterns')
    analyze_parser.add_argument("--epochs", nargs='+', required=True, help="Epochs to analyze")
    analyze_parser.add_argument("--output", help="Output file for analysis results (JSON)")
    analyze_parser.add_argument("--trends-only", action="store_true", help="Show only trend analysis")
    analyze_parser.add_argument("--tasks-only", action="store_true", help="Show only task progression")
    analyze_parser.add_argument("--patterns-only", action="store_true", help="Show only performance patterns")
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    if args.command == 'score':
        cmd_score(args)
    elif args.command == 'report':
        cmd_report(args)
    elif args.command == 'analyze':
        cmd_analyze(args)

if __name__ == "__main__":
    main()
