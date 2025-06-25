#!/usr/bin/env python3
"""
Test the metrics generation components
"""

import sys
import json
from pathlib import Path

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))
sys.path.insert(0, str(Path(__file__).parent / "evaluation" / "metrics-collectors"))

def test_metrics_components():
    """Test all metrics components work together"""
    print("🧪 Testing Metrics Components Integration")
    print("=" * 50)
    
    epoch_name = "epoch-001"
    
    try:
        # Test 1: Score Calculator
        print("1. Testing ScoreCalculator...")
        from score_calculator import ScoreCalculator
        calculator = ScoreCalculator()
        epoch_score = calculator.calculate_epoch_score(epoch_name)
        print(f"   ✅ Score calculated: {epoch_score.total_score}/{epoch_score.max_possible_score} ({epoch_score.success_rate:.1f}%)")
        
        # Test 2: Report Generator
        print("2. Testing ReportGenerator...")
        from report_generator import ReportGenerator
        generator = ReportGenerator()
        report_files = generator.generate_epoch_report(epoch_name)
        print(f"   ✅ Reports generated: {len(report_files)} files")
        for format_type, file_path in report_files.items():
            print(f"      - {format_type.upper()}: {Path(file_path).name}")
        
        # Test 3: Epoch Analyzer
        print("3. Testing EpochAnalyzer...")
        from epoch_analyzer import EpochAnalyzer
        analyzer = EpochAnalyzer()
        analysis = analyzer.analyze_epoch(epoch_name)
        print(f"   ✅ Analysis completed for {analysis['epoch_name']}")
        
        # Test 4: Integration Test (like evaluate_epoch.py does)
        print("4. Testing Integrated Metrics Generation...")
        
        metrics_summary = {
            'epoch_name': epoch_name,
            'generated_at': epoch_score.generated_at.isoformat(),
            'score_summary': {
                'total_score': epoch_score.total_score,
                'max_possible_score': epoch_score.max_possible_score,
                'success_rate': epoch_score.success_rate,
                'completed_tasks': epoch_score.completed_tasks,
                'total_tasks': epoch_score.total_tasks,
                'compilation_success_rate': epoch_score.compilation_success_rate,
                'test_success_rate': epoch_score.test_success_rate
            },
            'detailed_report': report_files,
            'analysis': analysis,
            'reports_generated': list(report_files.values())
        }
        
        print(f"   ✅ Integrated metrics summary:")
        print(f"      - Score: {metrics_summary['score_summary']['success_rate']:.1f}% success rate")
        print(f"      - Reports: {len(metrics_summary['reports_generated'])} files generated")
        print(f"      - Analysis: {len(analysis['recommendations'])} recommendations")
        
        # Test 5: Save summary like evaluate_epoch.py does
        print("5. Testing Summary Save...")
        summary_file = Path(__file__).parent / "epochs" / epoch_name / "test_metrics_summary.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, 'w') as f:
            json.dump(metrics_summary, f, indent=2, default=str)
        print(f"   ✅ Metrics summary saved to: {summary_file.name}")
        
        print("\n🎉 All metrics components working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_metrics_components()
    sys.exit(0 if success else 1)