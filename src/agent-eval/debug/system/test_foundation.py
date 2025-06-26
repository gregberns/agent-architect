#!/usr/bin/env python3
"""
End-to-end test of foundation components
"""

import os
import shutil
import subprocess
from pathlib import Path

def test_workspace_copying():
    """Test copying default workspaces to epoch runs"""
    print("Testing Workspace Copying...")
    
    # Define paths
    base_dir = Path(__file__).parent
    default_workspaces = base_dir / "default-workspaces"
    epoch_runs = base_dir / "epochs" / "epoch-001" / "runs"
    
    # Clear existing test tasks
    test_task = epoch_runs / "task-002"
    if test_task.exists():
        shutil.rmtree(test_task)
    
    # Test copying task-002 (calculator)
    source_task = default_workspaces / "task-002"
    if not source_task.exists():
        print("❌ Source task-002 not found")
        return False
    
    # Copy task
    shutil.copytree(source_task, test_task)
    
    # Verify structure
    required_files = [
        test_task / "input" / "TASK.md",
        test_task / "expected-output" / "calculator.py",
        test_task / "tests" / "test_calculator.py"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Missing required file: {file_path}")
            return False
    
    # Create output directory
    output_dir = test_task / "output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"✅ Successfully copied task-002 to epoch runs")
    print(f"   Source: {source_task}")
    print(f"   Target: {test_task}")
    print(f"   Files: {len(list(test_task.rglob('*')))} total")
    
    return True

def test_task_validation():
    """Test that default workspace tasks are valid"""
    print("\nTesting Task Validation...")
    
    base_dir = Path(__file__).parent
    default_workspaces = base_dir / "default-workspaces"
    
    if not default_workspaces.exists():
        print("❌ Default workspaces directory not found")
        return False
    
    # Get all task directories
    task_dirs = [d for d in default_workspaces.iterdir() if d.is_dir() and d.name.startswith('task-')]
    
    if not task_dirs:
        print("❌ No task directories found")
        return False
    
    print(f"   Found {len(task_dirs)} tasks to validate")
    
    valid_tasks = 0
    for task_dir in task_dirs:
        task_name = task_dir.name
        
        # Check required structure
        required_structure = [
            task_dir / "input" / "TASK.md",
            task_dir / "expected-output",
            task_dir / "tests"
        ]
        
        task_valid = True
        for required_path in required_structure:
            if not required_path.exists():
                print(f"   ❌ {task_name}: Missing {required_path.name}")
                task_valid = False
        
        if task_valid:
            # Check if expected output has python files
            expected_output = task_dir / "expected-output"
            py_files = list(expected_output.glob("*.py"))
            
            if py_files:
                print(f"   ✅ {task_name}: Valid structure, {len(py_files)} Python file(s)")
                valid_tasks += 1
            else:
                print(f"   ⚠️  {task_name}: No Python files in expected-output")
    
    if valid_tasks == len(task_dirs):
        print(f"✅ All {valid_tasks} tasks are valid")
        return True
    else:
        print(f"❌ Only {valid_tasks}/{len(task_dirs)} tasks are valid")
        return False

def test_docker_setup():
    """Test Docker setup without API calls"""
    print("\nTesting Docker Setup...")
    
    base_dir = Path(__file__).parent
    agent_src = base_dir / "epochs" / "epoch-001" / "agent-src"
    
    if not agent_src.exists():
        print("❌ Agent source directory not found")
        return False
    
    # Check required Docker files
    required_files = [
        agent_src / "Dockerfile",
        agent_src / "docker-compose.yml",
        agent_src / "requirements.txt",
        agent_src / "agent.py"
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Missing Docker file: {file_path.name}")
            return False
    
    print("✅ All Docker files present")
    
    # Test Docker build (but don't run to avoid API calls)
    try:
        os.chdir(agent_src)
        result = subprocess.run(
            ["docker", "build", ".", "-t", "agent-test"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Docker image builds successfully")
            
            # Clean up the test image
            subprocess.run(["docker", "rmi", "agent-test"], capture_output=True)
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker build timed out")
        return False
    except FileNotFoundError:
        print("⚠️  Docker not available - skipping build test")
        return True  # Don't fail the test if Docker isn't available

def test_orchestrator_import():
    """Test that orchestrator modules can be imported"""
    print("\nTesting Orchestrator Module Imports...")
    
    try:
        # Test importing orchestrator modules
        import sys
        orchestrator_path = Path(__file__).parent / "orchestrator"
        sys.path.insert(0, str(orchestrator_path))
        
        from job_queue import JobQueue, JobType, JobStatus, JobResult
        from config_simple import load_config, OrchestratorConfig
        
        print("✅ All orchestrator modules imported successfully")
        
        # Test basic functionality
        config = OrchestratorConfig.default()
        queue = JobQueue("test_queue.json")
        
        # Clean up test file
        test_file = Path("test_queue.json")
        if test_file.exists():
            test_file.unlink()
        
        print("✅ Orchestrator components functional")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Orchestrator test error: {e}")
        return False

def main():
    """Run all foundation tests"""
    print("🧪 Testing Agent Evaluation Foundation Components")
    print("=" * 60)
    
    tests = [
        test_workspace_copying,
        test_task_validation,
        test_docker_setup,
        test_orchestrator_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All foundation tests passed! Ready for next phase.")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)