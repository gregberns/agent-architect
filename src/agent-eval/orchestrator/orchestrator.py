#!/usr/bin/env python3
"""
Main orchestrator for agent evaluation system.
Manages job queue and worker processes.
"""
import sys

def main():
    """Main CLI interface"""
    print("DEPRECATION NOTICE")
    print("="*60)
    print("The orchestrator.py daemon has been deprecated and is no longer needed.")
    print("The evaluation system is now managed directly by 'evaluate_epoch.py'.")
    print("\nTo run an evaluation, please use the following command:")
    print("  python3 orchestrator/evaluate_epoch.py --epoch <epoch_name>\n")
    print("All functionality, including parallel task execution, is handled by that script.")
    print("="*60)
    sys.exit(1)

if __name__ == "__main__":
    main()
