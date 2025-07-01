#!/usr/bin/env python3
"""
Generate MBPP Tasks - Convert MBPP dataset entries into evaluation tasks
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List


class MBPPTaskGenerator:
    """Generates evaluation tasks from MBPP dataset"""
    
    def __init__(self, mbpp_file: str, output_dir: str):
        self.mbpp_file = Path(mbpp_file)
        self.output_dir = Path(output_dir)
        
        if not self.mbpp_file.exists():
            raise FileNotFoundError(f"MBPP file not found: {mbpp_file}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_mbpp_data(self) -> List[Dict[str, Any]]:
        """Load MBPP data from JSONL file"""
        data = []
        with open(self.mbpp_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        return data
    
    def generate_task_range(self, start_id: int, end_id: int) -> None:
        """Generate tasks for a specific range of MBPP task IDs"""
        print(f"🔄 Loading MBPP data from {self.mbpp_file}")
        mbpp_data = self.load_mbpp_data()
        
        # Create lookup by task_id
        mbpp_lookup = {item['task_id']: item for item in mbpp_data}
        
        generated_count = 0
        for task_id in range(start_id, end_id + 1):
            if task_id in mbpp_lookup:
                self._generate_single_task(mbpp_lookup[task_id])
                generated_count += 1
            else:
                print(f"⚠️  Warning: MBPP task {task_id} not found in dataset")
        
        print(f"✅ Generated {generated_count} tasks from range {start_id}-{end_id}")
    
    def _generate_single_task(self, mbpp_item: Dict[str, Any]) -> None:
        """Generate a single task from MBPP item"""
        task_id = mbpp_item['task_id']
        task_name = f"mbpp-task-{task_id:03d}"
        task_dir = self.output_dir / task_name
        
        # Create task directory structure
        task_dir.mkdir(exist_ok=True)
        (task_dir / "input").mkdir(exist_ok=True)
        (task_dir / "tests").mkdir(exist_ok=True)
        (task_dir / "expected-output").mkdir(exist_ok=True)
        
        # Generate TASK.md
        self._create_task_md(task_dir, mbpp_item)
        
        # Generate test file
        self._create_test_file(task_dir, mbpp_item)
        
        # Generate expected output (reference solution)
        self._create_expected_output(task_dir, mbpp_item)
        
        # Save source JSON for reference
        self._save_source_json(task_dir, mbpp_item)
        
        print(f"📝 Generated task: {task_name}")
    
    def _create_task_md(self, task_dir: Path, mbpp_item: Dict[str, Any]) -> None:
        """Create TASK.md file"""
        task_id = mbpp_item['task_id']
        description = mbpp_item['text']
        
        # Extract function name from the test cases (more reliable)
        function_name = "solution"  # default
        test_list = mbpp_item.get('test_list', [])
        
        if test_list:
            # Look for function calls in test cases to find the main function being tested
            import re
            for test in test_list:
                # Extract function calls from assertions like "assert func_name(args) == result"
                match = re.search(r'assert\s+(\w+)\s*\(', test)
                if match:
                    potential_func = match.group(1)
                    # Check if this function exists in the code
                    if f'def {potential_func}(' in mbpp_item['code']:
                        function_name = potential_func
                        break
        
        # Fallback: extract first function name from code
        if function_name == "solution":
            code_lines = mbpp_item['code'].split('\n')
            for line in code_lines:
                if line.strip().startswith('def '):
                    func_def = line.strip()[4:].split('(')[0].strip()
                    if func_def and func_def.isidentifier():
                        function_name = func_def
                        break
        
        task_content = f"""# Task MBPP-{task_id:03d}

## Objective
{description}

## Requirements
1. Create a function named `{function_name}()` that satisfies the test cases
2. Write the function to `./output/{function_name}.py`
3. Your function must pass all the provided test cases

## Expected Test Cases
Your function will be tested with:
"""
        
        # Add test cases in a simpler format
        for test in mbpp_item.get('test_list', []):
            task_content += f"- {test}\n"
        
        task_content += f"""
## Scoring Criteria
- **Compilation (1 point)**: Python script runs without syntax errors
- **Test Validation (1 point)**: Function exists and passes all test cases

Write your solution directly to the output file."""
        
        with open(task_dir / "input" / "TASK.md", 'w') as f:
            f.write(task_content)
    
    def _create_test_file(self, task_dir: Path, mbpp_item: Dict[str, Any]) -> None:
        """Create test file with pytest tests"""
        task_id = mbpp_item['task_id']
        
        # Extract function name from the test cases (more reliable)
        function_name = "solution"  # default
        test_list = mbpp_item.get('test_list', [])
        
        if test_list:
            # Look for function calls in test cases to find the main function being tested
            import re
            for test in test_list:
                # Extract function calls from assertions like "assert func_name(args) == result"
                match = re.search(r'assert\s+(\w+)\s*\(', test)
                if match:
                    potential_func = match.group(1)
                    # Check if this function exists in the code
                    if f'def {potential_func}(' in mbpp_item['code']:
                        function_name = potential_func
                        break
        
        # Fallback: extract first function name from code
        if function_name == "solution":
            code_lines = mbpp_item['code'].split('\n')
            for line in code_lines:
                if line.strip().startswith('def '):
                    func_def = line.strip()[4:].split('(')[0].strip()
                    if func_def and func_def.isidentifier():
                        function_name = func_def
                        break
        
        module_name = function_name
        
        test_content = f"""import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_function_exists():
    \"\"\"Test that the required function exists\"\"\"
    try:
        import {module_name}
        assert hasattr({module_name}, '{function_name}'), "{function_name} function not found"
    except ImportError:
        pytest.fail("{module_name}.py file not found in output directory")

"""
        
        # Add individual test functions
        for i, test in enumerate(mbpp_item.get('test_list', []), 1):
            # Clean up the test assertion and fix function calls
            test_clean = test.replace('assert ', '').strip()
            # Replace bare function calls with module.function calls
            test_clean = test_clean.replace(f'{function_name}(', f'{module_name}.{function_name}(')
            
            test_content += f"""def test_case_{i}():
    \"\"\"Test case {i}: {test}\"\"\"
    import {module_name}
    assert {test_clean}

"""
        
        # Add setup code if present
        if mbpp_item.get('test_setup_code'):
            test_content += f"""
# Test setup code
{mbpp_item['test_setup_code']}
"""
        
        with open(task_dir / "tests" / f"test_{module_name}.py", 'w') as f:
            f.write(test_content)
    
    def _create_expected_output(self, task_dir: Path, mbpp_item: Dict[str, Any]) -> None:
        """Create expected output (reference solution)"""
        # Extract function name from the test cases (more reliable)
        function_name = "solution"  # default
        test_list = mbpp_item.get('test_list', [])
        
        if test_list:
            # Look for function calls in test cases to find the main function being tested
            import re
            for test in test_list:
                # Extract function calls from assertions like "assert func_name(args) == result"
                match = re.search(r'assert\s+(\w+)\s*\(', test)
                if match:
                    potential_func = match.group(1)
                    # Check if this function exists in the code
                    if f'def {potential_func}(' in mbpp_item['code']:
                        function_name = potential_func
                        break
        
        # Fallback: extract first function name from code
        if function_name == "solution":
            code_lines = mbpp_item['code'].split('\n')
            for line in code_lines:
                if line.strip().startswith('def '):
                    func_def = line.strip()[4:].split('(')[0].strip()
                    if func_def and func_def.isidentifier():
                        function_name = func_def
                        break
        
        # Clean up the reference code (fix Windows line endings)
        cleaned_code = mbpp_item['code'].replace('\r\n', '\n').replace('\r', '\n')
        
        with open(task_dir / "expected-output" / f"{function_name}.py", 'w') as f:
            f.write(cleaned_code)
    
    def _save_source_json(self, task_dir: Path, mbpp_item: Dict[str, Any]) -> None:
        """Save the original MBPP JSON for reference"""
        with open(task_dir / "mbpp_source.json", 'w') as f:
            json.dump(mbpp_item, f, indent=2)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Generate evaluation tasks from MBPP dataset")
    parser.add_argument("--mbpp-file", default="./data/mbpp.jsonl", 
                       help="Path to MBPP JSONL file")
    parser.add_argument("--output-dir", default="./default-workspaces", 
                       help="Directory to generate tasks in")
    parser.add_argument("--start-id", type=int, required=True,
                       help="Starting MBPP task ID")
    parser.add_argument("--end-id", type=int, required=True,
                       help="Ending MBPP task ID (inclusive)")
    
    args = parser.parse_args()
    
    if args.start_id > args.end_id:
        print("❌ Error: start-id must be <= end-id")
        sys.exit(1)
    
    try:
        generator = MBPPTaskGenerator(args.mbpp_file, args.output_dir)
        generator.generate_task_range(args.start_id, args.end_id)
        print(f"🎉 Task generation completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
