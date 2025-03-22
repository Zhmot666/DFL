#!/usr/bin/env python
"""
Test runner for JSON Schema Validator application
Run this script to execute all tests
"""

import unittest
import sys
import os

def run_tests():
    """Run all test cases from the tests directory"""
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Discover all tests in the tests directory
    test_suite = loader.discover(os.path.join(current_dir, 'tests'), pattern='test_*.py')
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(test_suite)
    
    # Return the number of failures and errors as exit code
    return len(result.failures) + len(result.errors)

if __name__ == '__main__':
    sys.exit(run_tests()) 