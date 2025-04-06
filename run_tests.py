#!/usr/bin/env python
"""
Test runner script for GraphNIST.

This script runs all tests using pytest and generates a report.
"""

import sys
import os
import subprocess

def run_tests():
    """Run all tests using pytest."""
    print("Running GraphNIST tests...")
    
    # Run pytest with verbose output and show which tests are being run
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "-v",                  # Verbose output
        "--tb=short",          # Shorter traceback format
        "--color=yes",         # Colored output
        "--no-header",         # No header
    ], capture_output=True, text=True)
    
    # Print output
    print("\n== Test Results ==\n")
    print(result.stdout)
    
    if result.stderr:
        print("\n== Errors ==\n")
        print(result.stderr)
    
    # Return exit code
    return result.returncode

def run_unit_tests():
    """Run only unit tests."""
    print("Running unit tests...")
    
    # Run pytest with the unit marker
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "-v",                  # Verbose output
        "-m", "unit",          # Only run unit tests
        "--tb=short",          # Shorter traceback format
        "--color=yes",         # Colored output
    ], capture_output=True, text=True)
    
    # Print output
    print("\n== Unit Test Results ==\n")
    print(result.stdout)
    
    if result.stderr:
        print("\n== Errors ==\n")
        print(result.stderr)
    
    # Return exit code
    return result.returncode

if __name__ == "__main__":
    # Check if we should run specific tests
    if len(sys.argv) > 1 and sys.argv[1] == "unit":
        exit_code = run_unit_tests()
    else:
        exit_code = run_tests()
    
    # Exit with the same code as pytest
    sys.exit(exit_code) 