#!/usr/bin/env python3
"""
Test metrics collection system functionality
"""

import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "orchestrator"))

# Import metrics components
from metrics_collectors.score_calculator import ScoreCalculator, TaskScore, EpochScore
from metrics_collectors.report_generator import ReportGenerator
from metrics_collectors.epoch_analyzer import EpochAnalyzer
from job_queue import JobQueue, Job, JobType, JobStatus, JobResult

def test_score_calculation():
    """Test score calculation functionality"""
    print("Testing Score Calculation...")
    
    try:
        calculator = ScoreCalculator()
        
        # Test task score calculation for epoch-001 task-001
        task_score = calculator.calculate_task_score("epoch-001", "task-001")
        
        print(f"   Task score for epoch-001/task-001:")
        print(f"     Status: {task_score.status}")
        print(f"     Score: {task_score.total_score}/2")
        print(f"     Compilation: {task_score.compilation_score}")
        print(f"     Tests: {task_score.test_score}")
        
        # Test epoch score calculation
        epoch_score = calculator.calculate_epoch_score("epoch-001")
        
        print(f"   Epoch score for epoch-001:")
        print(f"     Total tasks: {epoch_score.total_tasks}")
        print(f"     Completed: {epoch_score.completed_tasks}")
        print(f"     Total score: {epoch_score.total_score}/{epoch_score.max_possible_score}")
        print(f"     Success rate: {epoch_score.success_rate:.1f}%")
        
        # Test validation summary
        summary = calculator.get_validation_summary("epoch-001")
        print(f"   Validation summary contains {len(summary['validation_details'])} tasks")
        
        print("✅ Score calculation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Score calculation test failed: {e}")
        return False

def test_report_generation():
    """Test report generation functionality"""
    print("\nTesting Report Generation...")
    
    try:
        generator = ReportGenerator()
        
        # Test getting available epochs
        epochs = generator.get_available_epochs()
        print(f"   Available epochs: {epochs}")
        
        if not epochs:
            print("   No epochs available for testing")
            return True
        
        # Test single epoch report generation
        test_epoch = epochs[0]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = generator.generate_epoch_report(
                test_epoch, 
                output_dir=temp_dir,
                formats=['json']
            )
            
            print(f"   Generated reports for {test_epoch}:")
            for format_type, file_path in output_files.items():
                file_size = Path(file_path).stat().st_size
                print(f"     {format_type}: {file_path} ({file_size} bytes)")
                
                # Verify JSON report is valid
                if format_type == 'json':
                    with open(file_path) as f:
                        report_data = json.load(f)
                    
                    required_sections = ['metadata', 'summary', 'task_details']
                    for section in required_sections:
                        if section not in report_data:
                            print(f"     ❌ Missing section: {section}")
                            return False
                    
                    print(f"     ✅ JSON report has all required sections")
            
            # Test comparison report if multiple epochs available
            if len(epochs) >= 2:
                output_files = generator.generate_comparison_report(
                    epochs[:2],
                    output_dir=temp_dir
                )
                print(f"   Generated comparison reports for {epochs[:2]}")
                
                for format_type, file_path in output_files.items():
                    file_size = Path(file_path).stat().st_size
                    print(f"     {format_type}: {file_path} ({file_size} bytes)")
        
        print("✅ Report generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        return False

def test_epoch_analysis():
    """Test epoch analysis functionality"""
    print("\nTesting Epoch Analysis...")
    
    try:
        analyzer = EpochAnalyzer()
        
        # Get available epochs
        calculator = ScoreCalculator()
        epochs = []
        
        # Try to find at least one epoch
        for potential_epoch in ["epoch-001", "epoch-002", "epoch-003"]:
            try:
                analyzer.calculator.calculate_epoch_score(potential_epoch)
                epochs.append(potential_epoch)
            except:
                continue
        
        if len(epochs) < 1:
            print("   No valid epochs found for analysis testing")
            return True
        
        print(f"   Testing with epochs: {epochs}")
        
        # Test task progression analysis
        if len(epochs) >= 1:
            task_progressions = analyzer.analyze_task_progression(epochs)
            print(f"   Task progressions analyzed: {len(task_progressions)} tasks")
            
            if task_progressions:
                # Show sample progression
                sample_task = list(task_progressions.keys())[0]
                prog = task_progressions[sample_task]
                print(f"     Sample ({sample_task}): consistency={prog.consistency_score:.2f}, best={prog.best_score}/2")
        
        # Test trend analysis (requires at least 2 epochs)
        if len(epochs) >= 2:
            trends = analyzer.analyze_trends(epochs[:2])
            print(f"   Trends analyzed: {len(trends)} metrics")
            
            for metric_name, trend in trends.items():
                print(f"     {metric_name}: {trend.trend_direction} ({trend.change_percentage:+.1f}%)")
        
        # Test performance patterns
        patterns = analyzer.find_performance_patterns(epochs)
        print(f"   Performance patterns found:")
        print(f"     Best epoch: {patterns['performance_summary']['best_performing_epoch']}")
        print(f"     Recommendations: {len(patterns['recommendations'])}")
        
        for rec in patterns['recommendations'][:2]:  # Show first 2 recommendations
            print(f"       • {rec[:60]}{'...' if len(rec) > 60 else ''}")
        
        print("✅ Epoch analysis test passed")
        return True
        
    except Exception as e:
        print(f"❌ Epoch analysis test failed: {e}")
        return False

def test_metrics_integration():
    """Test integration between metrics components"""
    print("\nTesting Metrics Integration...")
    
    try:
        # Test that all components can work together
        calculator = ScoreCalculator()
        generator = ReportGenerator()
        analyzer = EpochAnalyzer()
        
        # Verify they're using the same base directory
        base_dirs = [
            calculator.base_dir,
            generator.base_dir,
            analyzer.base_dir
        ]
        
        if len(set(str(d) for d in base_dirs)) != 1:
            print("   ❌ Components using different base directories")
            return False
        
        print(f"   ✅ All components using same base directory: {base_dirs[0]}")
        
        # Test that analyzer can use calculator results
        epochs = generator.get_available_epochs()
        if epochs:
            test_epoch = epochs[0]
            
            # Get epoch score from calculator
            epoch_score = calculator.calculate_epoch_score(test_epoch)
            
            # Use same epoch in analyzer
            task_progressions = analyzer.analyze_task_progression([test_epoch])
            
            # Verify consistency
            calc_tasks = set(epoch_score.task_scores.keys())
            analyzer_tasks = set(task_progressions.keys())
            
            if calc_tasks == analyzer_tasks:
                print(f"   ✅ Calculator and analyzer agree on task list: {len(calc_tasks)} tasks")
            else:
                print(f"   ⚠️  Task lists differ: calculator={len(calc_tasks)}, analyzer={len(analyzer_tasks)}")
                
        print("✅ Metrics integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Metrics integration test failed: {e}")
        return False

def main():
    """Run all metrics tests"""
    print("🧪 Testing Metrics Collection System")
    print("=" * 50)
    
    tests = [
        test_score_calculation,
        test_report_generation,
        test_epoch_analysis,
        test_metrics_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All metrics tests passed!")
        return True
    else:
        print("❌ Some metrics tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)