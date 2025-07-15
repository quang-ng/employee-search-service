#!/usr/bin/env python3
"""
Test runner script for the employee search service
"""
import subprocess
import sys
import os
from app.config.logging import setup_logging
import structlog

setup_logging()
logger = structlog.get_logger()

def run_tests():
    """Run the test suite"""
    logger.info("test_start", msg="Running employee search service tests...")
    
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
        logger.info("test_success", msg="All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error("test_failed", exit_code=e.returncode)
        return e.returncode

if __name__ == "__main__":
    sys.exit(run_tests()) 