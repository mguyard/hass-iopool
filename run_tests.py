#!/usr/bin/env python3
"""Test runner for iopool integration tests."""

import sys
import unittest
import os

def run_tests():
    """Run all available tests."""
    # Add the custom_components directory to the Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components/iopool'))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/custom_components/iopool/', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())