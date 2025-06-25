#!/usr/bin/env python3
"""
Comprehensive test runner for the agent evaluation system

This script runs all tests and provides various testing modes:
- Unit tests: Test individual components
- Integration tests: Test component interactions  
- System tests: Test end-to-end workflows
- Recovery tests: Test error handling and recovery
- All tests: Run complete test suite
- Critical tests: Run essential tests quickly
- Pre-commit tests: Quick validation for commits
"""

import sys
import os
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add test modules to path
TEST_DIR = Path(__file__).parent
sys.path.insert(0, str(TEST_DIR / "fixtures"))
sys.path.insert(0, str(TEST_DIR.parent / "orchestrator"))

from utilities import TestResults, print_test_summary


def run_unit_tests() -> TestResults:
    """Run all unit tests"""
    print("🔬 UNIT TESTS")
    print("=" * 60)
    
    # Import and run unit tests
    results = []
    
    try:
        from unit.test_job_queue import run_job_queue_tests
        results.append(run_job_queue_tests())
    except ImportError as e:
        print(f"❌ Failed to import job queue tests: {e}")
        results.append(TestResults(0, 1, [f"Job queue import error: {e}"], 0))
    
    try:
        from unit.test_metrics_generation import run_metrics_generation_tests
        results.append(run_metrics_generation_tests())
    except ImportError as e:
        print(f"❌ Failed to import metrics generation tests: {e}")
        results.append(TestResults(0, 1, [f"Metrics import error: {e}"], 0))
    
    # Combine all unit test results
    return combine_results(results)


def run_integration_tests() -> TestResults:
    """Run all integration tests"""
    print("\n🔗 INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        from integration.test_orchestrator_workers import run_orchestrator_worker_tests
        results = run_orchestrator_worker_tests()
        return results
    except ImportError as e:
        print(f"❌ Failed to import integration tests: {e}")
        return TestResults(0, 1, [f"Import error: {e}"], 0)


def run_system_tests() -> TestResults:
    """Run all system tests"""
    print("\n🏗️ SYSTEM TESTS")
    print("=" * 60)
    
    # Placeholder for system tests - to be implemented
    print("  System tests not yet implemented")
    return TestResults(0, 0, [], 0)


def run_recovery_tests() -> TestResults:
    """Run all recovery tests"""
    print("\n🚨 RECOVERY TESTS")
    print("=" * 60)
    
    try:
        from recovery.test_queue_corruption import run_queue_corruption_tests
        results = run_queue_corruption_tests()
        return results
    except ImportError as e:
        print(f"❌ Failed to import recovery tests: {e}")
        return TestResults(0, 1, [f"Import error: {e}"], 0)


def run_stress_tests() -> TestResults:
    """Run all stress tests"""
    print("\n💪 STRESS TESTS")
    print("=" * 60)
    
    # Placeholder for stress tests - to be implemented
    print("  Stress tests not yet implemented")
    return TestResults(0, 0, [], 0)


def combine_results(results_list: List[TestResults]) -> TestResults:
    """Combine multiple test results"""
    total_passed = sum(r.passed for r in results_list)
    total_failed = sum(r.failed for r in results_list)
    all_errors = []
    for r in results_list:
        all_errors.extend(r.errors)
    total_time = sum(r.execution_time for r in results_list)
    
    return TestResults(
        passed=total_passed,
        failed=total_failed,
        errors=all_errors,
        execution_time=total_time
    )


def run_all_tests() -> TestResults:
    """Run complete test suite"""
    print("🧪 RUNNING COMPLETE TEST SUITE")
    print("=" * 80)
    
    start_time = time.time()
    
    results = []
    
    # Run each test category
    results.append(run_unit_tests())
    results.append(run_integration_tests())
    results.append(run_system_tests())
    results.append(run_recovery_tests())
    results.append(run_stress_tests())
    
    combined = combine_results(results)
    
    print(f"\n🏁 COMPLETE TEST SUITE FINISHED")
    print("=" * 80)
    
    return combined


def run_critical_tests() -> TestResults:
    """Run essential tests quickly (for CI/monitoring)"""
    print("⚡ RUNNING CRITICAL TESTS")
    print("=" * 60)
    
    results = []
    
    # Only run core unit tests and basic integration
    results.append(run_unit_tests())
    results.append(run_integration_tests())
    
    combined = combine_results(results)
    
    print(f"\n⚡ CRITICAL TESTS FINISHED")
    print("=" * 60)
    
    return combined


def run_pre_commit_tests() -> TestResults:
    """Run quick validation tests for pre-commit hooks"""
    print("🚀 RUNNING PRE-COMMIT TESTS")
    print("=" * 60)
    
    # Run only essential unit tests
    results = run_unit_tests()
    
    print(f"\n🚀 PRE-COMMIT TESTS FINISHED")
    print("=" * 60)
    
    return results


def validate_test_environment():
    """Validate that test environment is properly set up"""
    print("🔍 Validating test environment...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required, found {sys.version}")
    
    # Check required directories exist
    required_dirs = [
        TEST_DIR / "unit",
        TEST_DIR / "integration", 
        TEST_DIR / "system",
        TEST_DIR / "recovery",
        TEST_DIR / "stress",
        TEST_DIR / "fixtures"
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            issues.append(f"Missing test directory: {dir_path}")
    
    # Check orchestrator modules can be imported
    try:
        from job_queue import JobQueue
        from config_simple import load_config
    except ImportError as e:
        issues.append(f"Cannot import orchestrator modules: {e}")
    
    if issues:
        print("❌ Test environment issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Test environment is properly set up")
        return True


def generate_test_report(results: TestResults, output_file: Optional[str] = None):
    """Generate detailed test report"""
    report_lines = [
        "# Agent Evaluation System - Test Report",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- Total Tests: {results.passed + results.failed}",
        f"- Passed: {results.passed}",
        f"- Failed: {results.failed}",
        f"- Success Rate: {(results.passed/(results.passed+results.failed)*100 if results.passed+results.failed > 0 else 0):.1f}%",
        f"- Execution Time: {results.execution_time:.2f}s",
        ""
    ]
    
    if results.errors:
        report_lines.extend([
            "## Failures and Errors",
            ""
        ])
        
        for i, error in enumerate(results.errors, 1):
            report_lines.extend([
                f"### Error {i}",
                "```",
                error,
                "```",
                ""
            ])
    else:
        report_lines.append("✅ All tests passed!")
    
    report_content = "\n".join(report_lines)
    
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)
        print(f"📄 Test report saved to: {output_path}")
    else:
        print("\n" + report_content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Agent Evaluation System Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all              # Run complete test suite
  python run_tests.py --critical         # Run essential tests
  python run_tests.py --pre-commit       # Quick validation
  python run_tests.py --unit             # Unit tests only
  python run_tests.py --integration      # Integration tests only
  python run_tests.py --recovery         # Recovery tests only
  python run_tests.py --report out.md    # Generate test report
        """
    )
    
    # Test selection arguments
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument('--all', action='store_true', help='Run complete test suite')
    test_group.add_argument('--critical', action='store_true', help='Run essential tests only')
    test_group.add_argument('--pre-commit', action='store_true', help='Run pre-commit validation tests')
    test_group.add_argument('--unit', action='store_true', help='Run unit tests only')
    test_group.add_argument('--integration', action='store_true', help='Run integration tests only')
    test_group.add_argument('--system', action='store_true', help='Run system tests only')
    test_group.add_argument('--recovery', action='store_true', help='Run recovery tests only')
    test_group.add_argument('--stress', action='store_true', help='Run stress tests only')
    
    # Output options
    parser.add_argument('--report', metavar='FILE', help='Generate test report to file')
    parser.add_argument('--validate-env', action='store_true', help='Validate test environment only')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Validate environment if requested
    if args.validate_env:
        valid = validate_test_environment()
        sys.exit(0 if valid else 1)
    
    # Validate test environment before running tests
    if not validate_test_environment():
        print("❌ Test environment validation failed")
        sys.exit(1)
    
    # Determine which tests to run
    if args.all:
        results = run_all_tests()
    elif args.critical:
        results = run_critical_tests()
    elif args.pre_commit:
        results = run_pre_commit_tests()
    elif args.unit:
        results = run_unit_tests()
    elif args.integration:
        results = run_integration_tests()
    elif args.system:
        results = run_system_tests()
    elif args.recovery:
        results = run_recovery_tests()
    elif args.stress:
        results = run_stress_tests()
    else:
        # Default to critical tests
        results = run_critical_tests()
    
    # Print summary
    if not args.quiet:
        print_test_summary(results)
    
    # Generate report if requested
    if args.report:
        generate_test_report(results, args.report)
    
    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()