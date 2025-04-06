#!/usr/bin/env python3
"""
Test runner for boundary tests.

This script runs the boundary resize tests and starts the manual boundary test.
"""

import unittest
import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_automated_tests():
    """Run the automated boundary resize tests."""
    print("Running automated boundary tests...")
    
    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover('.', pattern='test_boundary_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()

def run_manual_test():
    """Run the manual boundary test application."""
    print("\nStarting manual boundary test application...")
    print("This will open in a new window. Close it when you're done testing.")
    
    # Run the manual test script
    try:
        subprocess.run([sys.executable, 'manual_boundary_test.py'], 
                       cwd=os.path.dirname(os.path.abspath(__file__)))
        return True
    except Exception as e:
        print(f"Error running manual test: {e}")
        return False

if __name__ == "__main__":
    # First run the automated tests
    tests_passed = run_automated_tests()
    
    if tests_passed:
        print("\nAll automated tests passed!")
    else:
        print("\nSome automated tests failed. Fix issues before continuing.")
        sys.exit(1)
    
    # Ask user if they want to run the manual test
    response = input("\nDo you want to run the manual boundary test? (y/n): ")
    if response.lower() in ['y', 'yes']:
        run_manual_test()
    
    print("\nTesting complete!") 