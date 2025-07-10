#!/usr/bin/env python3
"""
Test runner script for the employee search service
"""
import subprocess
import sys
import os

def run_tests():
    """Run the test suite"""
    print("Running employee search service tests...")
    
    # Set environment variables for testing
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--asyncio-mode=auto'
    ]
    
    try:
        result = subprocess.run(cmd, env=env, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(run_tests()) 