#!/usr/bin/env python3
"""
Epoch Analyzer - advanced comparison and trend analysis across epochs
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))

from score_calculator import ScoreCalculator, EpochScore, TaskScore

@dataclass
class TrendAnalysis:
    """Trend analysis for a metric across epochs"""
    metric_name: str
    values: List[float]
    epochs: List[str]
    trend_direction: str  # "improving", "declining", "stable"
    change_percentage: float
    best_epoch: str
    worst_epoch: str
    
    def __init__(self, metric_name: str, values: List[float], epochs: List[str]):
        self.metric_name = metric_name
        self.values = values
        self.epochs = epochs

        if len(self.values) < 2:
            self.trend_direction = "insufficient_data"
            self.change_percentage = 0
            self.best_epoch = self.epochs[0] if self.epochs else "N/A"
            self.worst_epoch = self.epochs[0] if self.epochs else "N/A"
            return
        
        # Calculate trend
        first_val = self.values[0]
        last_val = self.values[-1]
        
        if last_val > first_val * 1.05:  # >5% improvement
            self.trend_direction = "improving"
        elif last_val < first_val * 0.95:  # >5% decline
            self.trend_direction = "declining"
        else:
            self.trend_direction = "stable"
        
        self.change_percentage = ((last_val - first_val) / first_val) * 100 if first_val > 0 else float('inf') if last_val > 0 else 0.0
        
        # Find best and worst epochs
        max_val = max(self.values)
        min_val = min(self.values)
        self.best_epoch = self.epochs[self.values.index(max_val)]
        self.worst_epoch = self.epochs[self.values.index(min_val)]

@dataclass
class TaskProgression:
    """Track a specific task's performance across epochs"""
    task_name: str
    epoch_scores: Dict[str, int]  # epoch -> score
    epoch_statuses: Dict[str, str]  # epoch -> status
    best_score: int
    best_epoch: str
    consistency_score: float  # 0-1, how consistent the task performance is
    
    def __init__(self, task_name: str, epoch_scores: Dict[str, int], epoch_statuses: Dict[str, str]):
        self.task_name = task_name
        self.epoch_scores = epoch_scores
        self.epoch_statuses = epoch_statuses
        
        if self.epoch_scores:
            scores = list(self.epoch_scores.values())
            self.best_score = max(scores)
            best_epochs = [epoch for epoch, score in self.epoch_scores.items() if score == self.best_score]
            self.best_epoch = best_epochs[0] if best_epochs else "none"
            
            # Calculate consistency (how often the task gets max score)
            max_scores = sum(1 for score in scores if score == 3) # Max score is 3
            self.consistency_score = max_scores / len(scores) if scores else 0.0
        else:
            self.best_score = 0
            self.best_epoch = "none"
            self.consistency_score = 0.0

class EpochAnalyzer:
    """Advanced analysis and comparison across epochs"""
    
    def __init__(self, config_path: str = None):
        self.calculator = ScoreCalculator(config_path)
        self.base_dir = Path(__file__).parent.parent.parent
    
    def analyze_trends(self, epochs: List[str]) -> Dict[str, TrendAnalysis]:
        """
        Analyze trends across multiple epochs
        
        Returns:
            Dictionary mapping metric names to trend analysis
        """
        if len(epochs) < 2:
            print("Warning: Need at least 2 epochs for trend analysis. Returning empty analysis.")
            return {}
        
        # Calculate scores for all epochs
        epoch_scores = {}
        for epoch in epochs:
            try:
                epoch_scores[epoch] = self.calculator.calculate_epoch_score(epoch)
            except Exception as e:
                print(f"Warning: Could not calculate score for {epoch}: {e}")
        
        valid_epochs = list(epoch_scores.keys())
        if len(valid_epochs) < 2:
            print("Warning: Need at least 2 valid epochs for trend analysis. Returning empty analysis.")
            return {}
        
        # Sort epochs for chronological analysis
        sorted_epochs = sorted(valid_epochs)
        
        # Extract metrics for trend analysis
        trends = {}
        
        metric_mappers = {
            'success_rate': ('Overall Success Rate', lambda s: s.success_rate),
            'compilation_success_rate': ('Compilation Success Rate', lambda s: s.compilation_success_rate),
            'test_success_rate': ('Test Success Rate', lambda s: s.test_success_rate),
            'total_score': ('Total Score', lambda s: float(s.total_score))
        }

        for key, (name, mapper) in metric_mappers.items():
            values = [mapper(epoch_scores[epoch]) for epoch in sorted_epochs]
            trends[key] = TrendAnalysis(
                metric_name=name,
                values=values,
                epochs=sorted_epochs
            )
        
        return trends
    
    def analyze_task_progression(self, epochs: List[str]) -> Dict[str, TaskProgression]:
        """
        Analyze how individual tasks perform across epochs
        
        Returns:
            Dictionary mapping task names to progression analysis
        """
        # Get all task scores across epochs
        task_progressions = {}
        all_tasks = set()
        
        epoch_scores_cache = {}
        for epoch in epochs:
            try:
                epoch_score = self.calculator.calculate_epoch_score(epoch)
                epoch_scores_cache[epoch] = epoch_score
                all_tasks.update(epoch_score.task_scores.keys())
            except Exception as e:
                print(f"Warning: Could not analyze {epoch}: {e}")
        
        # Second pass: build progression for each task
        for task_name in sorted(all_tasks):
            epoch_scores = {}
            epoch_statuses = {}
            
            for epoch in epochs:
                if epoch in epoch_scores_cache:
                    epoch_score = epoch_scores_cache[epoch]
                    if task_name in epoch_score.task_scores:
                        task_score = epoch_score.task_scores[task_name]
                        epoch_scores[epoch] = task_score.total_score
                        epoch_statuses[epoch] = task_score.status
                    else:
                        epoch_scores[epoch] = 0
                        epoch_statuses[epoch] = "not_run"
                else:
                    epoch_scores[epoch] = 0
                    epoch_statuses[epoch] = "error"
            
            task_progressions[task_name] = TaskProgression(
                task_name=task_name,
                epoch_scores=epoch_scores,
                epoch_statuses=epoch_statuses
            )
        
        return task_progressions
    
    def find_performance_patterns(self, epochs: List[str]) -> Dict[str, Any]:
        """
        Identify performance patterns and insights
        
        Returns:
            Dictionary with various performance insights
        """
        task_progressions = self.analyze_task_progression(epochs)
        trends = self.analyze_trends(epochs)
        
        patterns = {
            'most_improved_tasks': [],
            'most_consistent_tasks': [],
            'problematic_tasks': [],
            'performance_summary': {},
            'recommendations': []
        }
        
        # Find most improved tasks
        improved_tasks = []
        for task_name, progression in task_progressions.items():
            if len(progression.epoch_scores) >= 2:
                epoch_list = sorted(progression.epoch_scores.keys())
                first_score = progression.epoch_scores[epoch_list[0]]
                last_score = progression.epoch_scores[epoch_list[-1]]
                improvement = last_score - first_score
                if improvement > 0:
                    improved_tasks.append((task_name, improvement))
        
        patterns['most_improved_tasks'] = sorted(improved_tasks, key=lambda x: x[1], reverse=True)[:3]
        
        # Find most consistent tasks
        consistent_tasks = [(name, prog.consistency_score) 
                          for name, prog in task_progressions.items()]
        patterns['most_consistent_tasks'] = sorted(consistent_tasks, key=lambda x: x[1], reverse=True)[:3]
        
        # Find problematic tasks (low consistency, low best score)
        problematic_tasks = []
        for name, prog in task_progressions.items():
            if prog.best_score < 3 and prog.consistency_score < 0.5:
                avg_score = statistics.mean(prog.epoch_scores.values()) if prog.epoch_scores else 0
                problematic_tasks.append((name, avg_score, prog.consistency_score))
        
        patterns['problematic_tasks'] = sorted(problematic_tasks, key=lambda x: (x[1], x[2]))[:3]
        
        # Performance summary
        patterns['performance_summary'] = {
            'trending_upward': sum(1 for trend in trends.values() if trend.trend_direction == 'improving'),
            'trending_downward': sum(1 for trend in trends.values() if trend.trend_direction == 'declining'),
            'stable_metrics': sum(1 for trend in trends.values() if trend.trend_direction == 'stable'),
            'best_performing_epoch': self._find_best_epoch(epochs),
            'total_epochs_analyzed': len(epochs)
        }
        
        # Generate recommendations
        patterns['recommendations'] = self._generate_recommendations(trends, task_progressions)
        
        return patterns
    
    def _find_best_epoch(self, epochs: List[str]) -> str:
        """Find the epoch with highest overall performance"""
        best_epoch = None
        best_score = -1
        
        for epoch in epochs:
            try:
                epoch_score = self.calculator.calculate_epoch_score(epoch)
                if epoch_score.success_rate > best_score:
                    best_score = epoch_score.success_rate
                    best_epoch = epoch
            except Exception:
                continue
        
        return best_epoch or "unknown"
    
    def _generate_recommendations(self, trends: Dict[str, TrendAnalysis], 
                                task_progressions: Dict[str, TaskProgression]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Check overall trends
        success_trend = trends.get('success_rate')
        if success_trend and success_trend.trend_direction == 'declining':
            recommendations.append("Overall success rate is declining. Review recent changes and consider reverting problematic modifications.")
        elif success_trend and success_trend.trend_direction == 'improving':
            recommendations.append("Success rate is improving. Continue current evolution strategy.")
        
        # Check compilation vs test performance
        comp_trend = trends.get('compilation_success_rate')
        test_trend = trends.get('test_success_rate')
        
        if comp_trend and test_trend:
            if comp_trend.trend_direction == 'improving' and test_trend.trend_direction == 'declining':
                recommendations.append("Code generation is improving but test quality is declining. Focus on test logic understanding.")
            elif comp_trend.trend_direction == 'declining' and test_trend.trend_direction == 'improving':
                recommendations.append("Test understanding is good but syntax errors increasing. Focus on code generation accuracy.")
        
        # Check task-specific issues
        low_consistency_tasks = [name for name, prog in task_progressions.items() 
                               if prog.consistency_score < 0.3]
        
        if len(low_consistency_tasks) > 2:
            recommendations.append(f"Multiple tasks show inconsistent performance: {', '.join(low_consistency_tasks[:3])}. Consider task-specific training.")
        
        # Check for stagnation
        stable_count = sum(1 for trend in trends.values() if trend.trend_direction == 'stable')
        if stable_count >= 3 and len(trends) > 0:
            recommendations.append("Performance has plateaued across multiple metrics. Consider new evolution strategies or increased exploration.")
        
        return recommendations
    
    def analyze_epoch(self, epoch_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a single epoch
        
        Returns:
            Dictionary with comprehensive epoch analysis
        """
        try:
            # Get basic epoch score
            epoch_score = self.calculator.calculate_epoch_score(epoch_name)
            
            analysis = {
                'epoch_name': epoch_name,
                'analyzed_at': datetime.now().isoformat(),
                'overall_performance': json.loads(json.dumps(epoch_score, default=lambda o: o.isoformat() if isinstance(o, datetime) else o.__dict__)),
                'task_breakdown': {},
                'performance_insights': {},
                'recommendations': []
            }
            
            # Analyze individual tasks
            for task_name, task_score in epoch_score.task_scores.items():
                analysis['task_breakdown'][task_name] = {
                    'status': task_score.status,
                    'total_score': task_score.total_score,
                    'compilation_score': task_score.compilation_score,
                    'test_score': task_score.test_score,
                    'error_message': task_score.error_message
                }
            
            # Generate performance insights
            analysis['performance_insights'] = {
                'strong_areas': [],
                'weak_areas': [],
                'completion_rate': (epoch_score.completed_tasks / epoch_score.total_tasks) * 100 if epoch_score.total_tasks > 0 else 0
            }
            
            # Identify strong and weak areas
            if epoch_score.compilation_success_rate >= 80:
                analysis['performance_insights']['strong_areas'].append('Code compilation')
            elif epoch_score.compilation_success_rate < 50:
                analysis['performance_insights']['weak_areas'].append('Code compilation')
                
            if epoch_score.test_success_rate >= 80:
                analysis['performance_insights']['strong_areas'].append('Test execution')
            elif epoch_score.test_success_rate < 50:
                analysis['performance_insights']['weak_areas'].append('Test execution')
            
            # Generate single-epoch recommendations
            if epoch_score.success_rate < 50:
                analysis['recommendations'].append("Overall performance is below 50%. Consider reviewing task complexity and agent capabilities.")
            elif epoch_score.success_rate >= 80:
                analysis['recommendations'].append("Strong performance achieved. Consider increasing task complexity for continued growth.")
            
            if epoch_score.compilation_success_rate < epoch_score.test_success_rate:
                analysis['recommendations'].append("Compilation issues are the primary blocker. Focus on syntax and API usage training.")
            elif epoch_score.test_success_rate < epoch_score.compilation_success_rate:
                analysis['recommendations'].append("Code compiles well but fails tests. Focus on logic and requirement understanding.")
            
            return analysis
            
        except Exception as e:
            return {
                'epoch_name': epoch_name,
                'analyzed_at': datetime.now().isoformat(),
                'error': f"Analysis failed: {e}",
            }

def main():
    """CLI interface for epoch analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze trends and patterns across epochs")
    parser.add_argument("--epochs", nargs='+', required=True, help="Epochs to analyze")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    parser.add_argument("--trends-only", action="store_true", help="Show only trend analysis")
    parser.add_argument("--tasks-only", action="store_true", help="Show only task progression")
    parser.add_argument("--patterns-only", action="store_true", help="Show only performance patterns")
    
    args = parser.parse_args()
    
    analyzer = EpochAnalyzer()
    
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
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
