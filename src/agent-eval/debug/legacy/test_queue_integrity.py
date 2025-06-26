#!/usr/bin/env python3
"""
Test script to check and fix job queue file integrity
"""

import json
import sys
from pathlib import Path

def check_queue_file():
    """Check if the job queue file is valid JSON"""
    
    queue_file = Path(__file__).parent / "job_queue.json"
    
    if not queue_file.exists():
        print("❌ Queue file does not exist")
        return False
    
    try:
        with open(queue_file, 'r') as f:
            content = f.read()
        
        if not content.strip():
            print("❌ Queue file is empty")
            return False
        
        data = json.loads(content)
        job_count = len(data.get('jobs', {}))
        print(f"✅ Queue file is valid JSON with {job_count} jobs")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Queue file has JSON corruption: {e}")
        print(f"   Error at line {e.lineno}, column {e.colno}")
        
        # Show some context around the error
        lines = content.split('\n')
        error_line = e.lineno - 1
        start = max(0, error_line - 2)
        end = min(len(lines), error_line + 3)
        
        print("   Context:")
        for i in range(start, end):
            marker = " -> " if i == error_line else "    "
            print(f"{marker}{i+1:3}: {lines[i]}")
        
        return False
    
    except Exception as e:
        print(f"❌ Error reading queue file: {e}")
        return False

def fix_queue_file():
    """Create a fresh, empty queue file"""
    
    queue_file = Path(__file__).parent / "job_queue.json"
    
    try:
        fresh_data = {
            "jobs": {},
            "saved_at": "2025-06-24T21:30:00.000000"
        }
        
        with open(queue_file, 'w') as f:
            json.dump(fresh_data, f, indent=2)
        
        print("✅ Created fresh queue file")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fresh queue file: {e}")
        return False

def main():
    """Main function"""
    
    print("🔍 Checking job queue file integrity...")
    
    if check_queue_file():
        print("📋 Queue file is healthy")
        sys.exit(0)
    else:
        print("🚨 Queue file has issues")
        
        response = input("Do you want to create a fresh queue file? (y/n): ")
        if response.lower() == 'y':
            if fix_queue_file():
                print("✅ Queue file fixed - restart orchestrator")
                sys.exit(0)
            else:
                print("❌ Failed to fix queue file")
                sys.exit(1)
        else:
            print("❌ Queue file issues not resolved")
            sys.exit(1)

if __name__ == "__main__":
    main()