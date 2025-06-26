#!/bin/bash
# Easy-to-run test execution system for the agent evaluation system
# This script provides simple commands to validate the system after changes

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Agent Evaluation System - Test Runner"
echo "========================================"

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  test              Run critical tests (recommended for routine validation)"
    echo "  test-all          Run complete test suite"
    echo "  test-quick        Run fast pre-commit tests"
    echo "  test-unit         Run unit tests only"
    echo "  test-integration  Run integration tests only"
    echo "  test-recovery     Run recovery tests only"
    echo "  validate          Just validate test environment"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./test_system.sh test          # Quick validation after changes"
    echo "  ./test_system.sh test-all      # Full test suite"
    echo "  ./test_system.sh validate      # Check test setup"
}

# Function to run tests with error handling
run_test_command() {
    local test_type="$1"
    echo "Running $test_type tests..."
    
    if python tests/run_tests.py "$test_type"; then
        echo "✅ $test_type tests PASSED"
        return 0
    else
        echo "❌ $test_type tests FAILED"
        echo ""
        echo "💡 Tips for debugging test failures:"
        echo "  - Check that orchestrator system is not running (python orchestrator/orchestrator.py --stop)"
        echo "  - Ensure no Docker containers are hanging (docker ps)"
        echo "  - Check for port conflicts"
        echo "  - Review test output above for specific error details"
        return 1
    fi
}

# Parse command line argument
COMMAND="${1:-test}"

case "$COMMAND" in
    "test"|"")
        echo "🎯 Running critical tests for routine validation..."
        run_test_command "--critical"
        ;;
        
    "test-all")
        echo "🔬 Running complete test suite..."
        run_test_command "--all"
        ;;
        
    "test-quick")
        echo "⚡ Running quick pre-commit tests..."
        run_test_command "--pre-commit"
        ;;
        
    "test-unit")
        echo "🧪 Running unit tests..."
        run_test_command "--unit"
        ;;
        
    "test-integration")
        echo "🔗 Running integration tests..."
        run_test_command "--integration"
        ;;
        
    "test-recovery")
        echo "🚨 Running recovery tests..."
        run_test_command "--recovery"
        ;;
        
    "validate")
        echo "🔍 Validating test environment..."
        if python tests/run_tests.py --validate-env; then
            echo "✅ Test environment is properly configured"
        else
            echo "❌ Test environment has issues"
            exit 1
        fi
        ;;
        
    "help"|"-h"|"--help")
        show_usage
        ;;
        
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac

echo ""
echo "🏁 Test execution completed!"
echo ""
echo "📚 For more information:"
echo "  - See TESTING_FRAMEWORK_PLAN.md for detailed testing strategy"
echo "  - Run './test_system.sh help' for all available commands"
echo "  - Check tests/run_tests.py --help for advanced options"