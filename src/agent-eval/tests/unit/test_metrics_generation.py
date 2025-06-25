#!/usr/bin/env python3
"""
Unit tests for metrics generation functionality
"""

import sys
import time
import json
from pathlib import Path

# Add fixtures to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation" / "metrics-collectors"))

from utilities import TestResults

class TestMetricsGeneration:
    """Test metrics generation components"""
    
    def test_score_calculator(self):
        """Test ScoreCalculator functionality"""
        from score_calculator import ScoreCalculator
        
        calculator = ScoreCalculator()
        epoch_score = calculator.calculate_epoch_score("epoch-001")
        
        # Verify basic properties
        assert epoch_score.epoch == "epoch-001"
        assert epoch_score.total_tasks >= 0
        assert 0 <= epoch_score.success_rate <= 100
        assert epoch_score.total_score >= 0
        assert epoch_score.max_possible_score >= 0
    
    def test_report_generator(self):
        """Test ReportGenerator functionality"""
        from report_generator import ReportGenerator
        
        generator = ReportGenerator()
        report_files = generator.generate_epoch_report("epoch-001")
        
        # Verify reports were generated
        assert isinstance(report_files, dict)
        assert 'json' in report_files
        assert 'csv' in report_files
        
        # Verify files exist
        for file_path in report_files.values():
            assert Path(file_path).exists()
            assert Path(file_path).stat().st_size > 0
    
    def test_epoch_analyzer(self):
        """Test EpochAnalyzer functionality"""
        from epoch_analyzer import EpochAnalyzer
        
        analyzer = EpochAnalyzer()
        analysis = analyzer.analyze_epoch("epoch-001")
        
        # Verify analysis structure
        assert 'epoch_name' in analysis
        assert 'overall_performance' in analysis
        assert 'task_breakdown' in analysis
        assert 'performance_insights' in analysis
        assert 'recommendations' in analysis
        
        assert analysis['epoch_name'] == "epoch-001"
        assert isinstance(analysis['recommendations'], list)
    
    def test_integrated_metrics_generation(self):
        """Test integrated metrics generation like evaluate_epoch.py"""
        from evaluate_epoch import EpochEvaluator
        
        evaluator = EpochEvaluator()
        
        # Test the metrics generation method directly
        metrics_summary = evaluator._generate_comprehensive_metrics("epoch-001")
        
        # Verify comprehensive structure
        assert 'epoch_name' in metrics_summary
        assert 'generated_at' in metrics_summary
        assert 'score_summary' in metrics_summary
        assert 'detailed_report' in metrics_summary
        assert 'analysis' in metrics_summary
        assert 'reports_generated' in metrics_summary
        
        # Verify no critical errors
        assert not metrics_summary.get('error')
        
        # Verify reports were actually generated
        assert len(metrics_summary['reports_generated']) > 0
        
        # Check that all report files exist
        for file_path in metrics_summary['reports_generated']:
            assert Path(file_path).exists()
    
    def test_metrics_error_handling(self):
        """Test metrics generation with invalid epoch"""
        from evaluate_epoch import EpochEvaluator
        
        evaluator = EpochEvaluator()
        
        # Test with non-existent epoch
        metrics_summary = evaluator._generate_comprehensive_metrics("epoch-999")
        
        # Should not raise exception, but should have error information
        assert 'epoch_name' in metrics_summary
        assert metrics_summary['epoch_name'] == "epoch-999"
        
        # May have errors in sub-components for non-existent epoch
        # But the overall structure should still be intact


def run_metrics_generation_tests():
    """Run all metrics generation tests"""
    print("🧪 Running Metrics Generation Tests")
    print("=" * 50)
    
    test_instance = TestMetricsGeneration()
    
    tests = [
        ('Score Calculator', test_instance.test_score_calculator),
        ('Report Generator', test_instance.test_report_generator),
        ('Epoch Analyzer', test_instance.test_epoch_analyzer),
        ('Integrated Metrics Generation', test_instance.test_integrated_metrics_generation),
        ('Metrics Error Handling', test_instance.test_metrics_error_handling),
    ]
    
    passed = 0
    failed = 0
    errors = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            print(f"  Running: {test_name}... ", end="")
            test_func()
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            errors.append(f"{test_name}: {e}")
            failed += 1
    
    execution_time = time.time() - start_time
    
    return TestResults(
        passed=passed,
        failed=failed,
        errors=errors,
        execution_time=execution_time
    )


if __name__ == "__main__":
    results = run_metrics_generation_tests()
    
    from utilities import print_test_summary
    print_test_summary(results)
    
    sys.exit(0 if results.failed == 0 else 1)