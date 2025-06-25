#!/usr/bin/env python3
"""
Demonstration of the self-contained evaluation system
Shows the complete workflow without orchestrator workers
"""

import sys
import json
from pathlib import Path

# Add orchestrator directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

def demo_self_contained_evaluation():
    """
    Demonstrate the complete self-contained evaluation process
    This simulates what evaluate_epoch.py does but without the worker system
    """
    print("🎯 Self-Contained Evaluation System Demo")
    print("=" * 60)
    
    epoch_name = "epoch-001"
    print(f"📋 Demonstrating evaluation of {epoch_name}")
    
    try:
        # Step 1: Initialize the evaluator
        print("\n1️⃣ Initializing EpochEvaluator...")
        from evaluate_epoch import EpochEvaluator
        evaluator = EpochEvaluator()
        print("   ✅ EpochEvaluator initialized")
        
        # Step 2: Demonstrate metrics generation
        print("\n2️⃣ Generating comprehensive metrics...")
        print("   This is what happens when --no-metrics is NOT used:")
        
        metrics_summary = evaluator._generate_comprehensive_metrics(epoch_name)
        
        # Step 3: Show the results
        print("\n3️⃣ Evaluation Results Summary:")
        print("   " + "="*50)
        
        if 'error' not in metrics_summary:
            score_summary = metrics_summary.get('score_summary', {})
            print(f"   📊 Overall Score: {score_summary.get('total_score', 'N/A')}/{score_summary.get('max_possible_score', 'N/A')}")
            print(f"   📈 Success Rate: {score_summary.get('success_rate', 'N/A'):.1f}%")
            print(f"   ✅ Completed Tasks: {score_summary.get('completed_tasks', 'N/A')}/{score_summary.get('total_tasks', 'N/A')}")
            print(f"   ⚙️  Compilation Success: {score_summary.get('compilation_success_rate', 'N/A'):.1f}%")
            print(f"   🧪 Test Success: {score_summary.get('test_success_rate', 'N/A'):.1f}%")
            print(f"   📁 Reports Generated: {len(metrics_summary.get('reports_generated', []))}")
            
            # Show analysis insights
            analysis = metrics_summary.get('analysis', {})
            if 'performance_insights' in analysis:
                insights = analysis['performance_insights']
                if insights.get('strong_areas'):
                    print(f"   💪 Strong Areas: {', '.join(insights['strong_areas'])}")
                if insights.get('weak_areas'):
                    print(f"   ⚠️  Weak Areas: {', '.join(insights['weak_areas'])}")
            
            # Show recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                print(f"   💡 Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                    print(f"      {i}. {rec}")
        else:
            print(f"   ❌ Error in metrics generation: {metrics_summary['error']}")
        
        # Step 4: Show file outputs
        print("\n4️⃣ Generated Files:")
        print("   " + "="*50)
        
        reports_generated = metrics_summary.get('reports_generated', [])
        if reports_generated:
            for i, file_path in enumerate(reports_generated, 1):
                file_info = Path(file_path)
                if file_info.exists():
                    size_kb = file_info.stat().st_size / 1024
                    print(f"   {i}. {file_info.name} ({size_kb:.1f} KB)")
                else:
                    print(f"   {i}. {file_info.name} (missing)")
        else:
            print("   No files generated")
        
        # Step 5: Show what a complete evaluation summary would look like
        print("\n5️⃣ Complete Self-Contained Evaluation Summary:")
        print("   " + "="*50)
        
        # This is what would be in evaluation_summary.json
        complete_summary = {
            'epoch': epoch_name,
            'total_tasks': score_summary.get('total_tasks', 0),
            'successful_tasks': score_summary.get('completed_tasks', 0),
            'failed_tasks': score_summary.get('total_tasks', 0) - score_summary.get('completed_tasks', 0),
            'overall_score': score_summary.get('total_score', 0),
            'max_possible_score': score_summary.get('max_possible_score', 0),
            'success_rate': score_summary.get('success_rate', 0),
            'metrics': metrics_summary,  # Complete metrics included
            'self_contained': True,
            'evaluation_complete': True
        }
        
        print(f"   📦 Evaluation Type: Self-Contained (metrics included)")
        print(f"   🔄 Process: Evaluation → Validation → Metrics → Analysis")
        print(f"   💾 Output: Complete summary with all metrics embedded")
        print(f"   🎯 Status: Ready for immediate analysis and reporting")
        
        print(f"\n✨ Self-contained evaluation demonstrates:")
        print(f"   • Automatic metrics generation after evaluation")
        print(f"   • Comprehensive scoring and analysis")
        print(f"   • Report generation with multiple formats")
        print(f"   • Performance insights and recommendations")
        print(f"   • Everything in a single evaluation pass")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_self_contained_evaluation()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Self-contained evaluation demo")
    sys.exit(0 if success else 1)