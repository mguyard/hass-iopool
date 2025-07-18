#!/usr/bin/env python3
"""Test runner for iopool integration tests."""

import sys
import unittest
import os

def run_tests():
    """Run all available tests."""
    # Add the custom_components directory to the Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components/iopool'))
    
    # List of working test modules
    test_modules = [
        'tests.custom_components.iopool.test_api_models',
        'tests.custom_components.iopool.test_const',
        'tests.custom_components.iopool.test_model_logic',
    ]
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
            print(f"✅ Loaded tests from {module}")
        except ImportError as e:
            print(f"❌ Failed to load {module}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())