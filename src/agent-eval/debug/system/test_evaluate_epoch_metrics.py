#!/usr/bin/env python3
"""
Test the enhanced evaluate_epoch.py metrics generation functionality
"""

import sys
import json
from pathlib import Path

# Add orchestrator directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def test_metrics_generation_method():
    """Test just the _generate_comprehensive_metrics method"""
    print("🧪 Testing EpochEvaluator Metrics Generation")
    print("=" * 50)
    
    try:
        from evaluate_epoch import EpochEvaluator
        
        # Create evaluator instance
        evaluator = EpochEvaluator()
        
        # Test the metrics generation method directly
        print("1. Testing _generate_comprehensive_metrics method...")
        metrics_summary = evaluator._generate_comprehensive_metrics("epoch-001")
        
        # Verify the structure
        assert 'epoch_name' in metrics_summary
        assert 'generated_at' in metrics_summary
        assert 'score_summary' in metrics_summary
        assert 'detailed_report' in metrics_summary  
        assert 'analysis' in metrics_summary
        assert 'reports_generated' in metrics_summary
        
        print(f"   ✅ Metrics generated successfully")
        print(f"      - Epoch: {metrics_summary['epoch_name']}")
        print(f"      - Score: {metrics_summary.get('score_summary', {}).get('success_rate', 'N/A')}% success rate")
        print(f"      - Reports: {len(metrics_summary['reports_generated'])} files")
        
        # Check for errors in sub-components
        score_error = metrics_summary.get('score_summary', {}).get('error')
        report_error = metrics_summary.get('detailed_report', {}).get('error') 
        analysis_error = metrics_summary.get('analysis', {}).get('error')
        
        if score_error:
            print(f"   ⚠️  Score calculation error: {score_error}")
        if report_error:
            print(f"   ⚠️  Report generation error: {report_error}")
        if analysis_error:
            print(f"   ⚠️  Analysis error: {analysis_error}")
        
        if not (score_error or report_error or analysis_error):
            print(f"   ✅ All metrics components working without errors")
            
        return True
        
    except Exception as e:
        print(f"❌ Metrics generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_metrics_generation_method()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Metrics generation test")
    sys.exit(0 if success else 1)