# Testing Documentation

## Overview

This document describes the testing infrastructure for the iopool Home Assistant integration.

## Test Structure

The test suite is organized following Home Assistant testing best practices:

```
tests/
├── custom_components/
│   └── iopool/
│       ├── __init__.py
│       ├── conftest.py           # Test fixtures and common utilities
│       ├── test_api_models.py    # Tests for API data models
│       ├── test_const.py         # Tests for constants
│       ├── test_coordinator.py   # Tests for data coordinator (pytest-based)
│       └── test_models.py        # Tests for configuration models
```

## Running Tests

### Local Testing

To run tests locally:

```bash
# Run all available tests
python3 run_tests.py

# Run specific test files
python3 -m unittest tests.custom_components.iopool.test_api_models -v
python3 -m unittest tests.custom_components.iopool.test_const -v
```

### CI/CD Testing

Tests are automatically run in GitHub Actions on:
- Pull requests to main/beta branches
- Pushes to main/beta branches
- Daily scheduled runs

## Test Categories

### Unit Tests

#### API Models Tests (`test_api_models.py`)
- Tests data parsing and conversion between API responses and Python objects
- Validates datetime parsing with different timezone formats
- Tests error handling for invalid data structures
- **Coverage**: 10 test cases covering all API models

#### Constants Tests (`test_const.py`)
- Validates all integration constants and configuration values
- Tests API endpoints and scan intervals
- Ensures proper data types and non-empty values
- **Coverage**: 8 test cases covering all constants

### Integration Tests (Planned)

The following tests require Home Assistant dependencies and will be added when pytest infrastructure is fully set up:

#### Coordinator Tests (`test_coordinator.py`)
- Tests data fetching from the iopool API
- Validates error handling for network issues
- Tests data caching and update mechanisms

#### Configuration Flow Tests
- Tests integration setup and configuration
- Validates user input validation
- Tests option updates and reloading

#### Entity Tests
- Tests sensor state updates and attributes
- Validates entity availability and device information
- Tests filtration automation logic

## Test Infrastructure

### Dependencies

Currently using Python's built-in `unittest` framework to avoid dependency issues. The full test suite will use:

```
pytest==7.4.4
pytest-asyncio==0.23.2
pytest-cov==4.1.0
pytest-homeassistant-custom-component==0.13.104
```

### Configuration

- `pytest.ini`: Configuration for pytest with coverage settings
- `requirements_test.txt`: Testing dependencies
- `conftest.py`: Common fixtures and test utilities

### Coverage

Current test coverage focuses on pure Python logic:
- ✅ API data models and parsing
- ✅ Constants and configuration values
- 🔄 Configuration data models (partial)
- ⏳ Home Assistant integration components (pending full HA environment)

## Current Status

### Working Tests (18 tests passing)
- API models: 10 tests ✅
- Constants: 8 tests ✅

### Pending Tests (requires Home Assistant dependencies)
- Coordinator tests
- Configuration flow tests
- Entity tests
- Integration setup/teardown tests

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't rely on external state
2. **Mock External Dependencies**: API calls and Home Assistant components are mocked
3. **Edge Case Testing**: Tests include error conditions and invalid inputs
4. **Clear Test Names**: Each test method clearly describes what it's testing
5. **Comprehensive Coverage**: Tests cover normal operation, edge cases, and error conditions

## Future Enhancements

1. **Add Home Assistant Test Environment**: Set up proper HA testing environment
2. **Integration Tests**: Add tests for full integration lifecycle
3. **Performance Tests**: Add tests for data update performance
4. **End-to-End Tests**: Add tests that simulate real API interactions
5. **Coverage Reports**: Generate and track test coverage metrics