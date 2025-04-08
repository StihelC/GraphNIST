#!/usr/bin/env python3
import unittest
import sys
import os

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test modules
from tests.test_properties_panel import TestPropertiesPanel
from tests.test_multi_device_properties import TestMultiDeviceProperties
from tests.test_bulk_property_edit import TestBulkPropertyEdit
from tests.test_context_menu import TestContextMenu

if __name__ == "__main__":
    # Create a test suite with all property-related tests
    test_suite = unittest.TestSuite()
    
    # Add all tests from each test class
    test_suite.addTest(unittest.makeSuite(TestPropertiesPanel))
    test_suite.addTest(unittest.makeSuite(TestMultiDeviceProperties))
    test_suite.addTest(unittest.makeSuite(TestBulkPropertyEdit))
    test_suite.addTest(unittest.makeSuite(TestContextMenu))
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(test_suite)
    
    # Exit with non-zero code if there were failures
    sys.exit(not result.wasSuccessful()) 