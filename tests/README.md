# iopool Home Assistant Integration Test Suite

A comprehensive test suite for the iopool Home Assistant custom integration following HA testing best practices.

## Quick Start

```bash
# Run all tests
python3 run_tests.py

# Run specific test modules
python3 -m unittest tests.custom_components.iopool.test_api_models -v
python3 -m unittest tests.custom_components.iopool.test_const -v
python3 -m unittest tests.custom_components.iopool.test_model_logic -v
```

## Test Coverage

✅ **26 tests passing** with 100% success rate

### Covered Components

- **API Models** (10 tests) - Data parsing and validation
- **Constants** (8 tests) - Configuration values and endpoints  
- **Model Logic** (8 tests) - Configuration data structures and parsing

### Test Categories

| Component | Tests | Coverage |
|-----------|-------|----------|
| `api_models.py` | 10 | ✅ Full |
| `const.py` | 8 | ✅ Full |
| Model logic | 8 | ✅ Core logic |
| **Total** | **26** | **100% success** |

## Architecture

```
tests/
├── custom_components/iopool/
│   ├── conftest.py              # Test fixtures (for pytest)
│   ├── test_api_models.py       # API response parsing tests
│   ├── test_const.py            # Constants validation tests
│   ├── test_coordinator.py      # Data coordinator tests (pytest-based)*
│   └── test_model_logic.py      # Configuration model tests
└── __init__.py
```

*\* Requires Home Assistant environment*

## Test Highlights

### API Models Testing
- JSON to Python object conversion
- DateTime parsing with timezone handling
- Error handling for invalid data
- Multiple pool support validation

### Constants Testing  
- API endpoint validation
- Configuration key verification
- Data type consistency checks
- Default values validation

### Model Logic Testing
- Configuration data parsing
- Time format conversion
- Duration calculations
- Error handling for invalid inputs

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main/beta branches  
- Daily scheduled runs

See `.github/workflows/home-assistant.yaml` for CI configuration.

## Development Guidelines

1. **Add tests for new features** - Every new component should include tests
2. **Test edge cases** - Include error conditions and invalid inputs
3. **Mock external dependencies** - Use mocks for API calls and HA components
4. **Keep tests isolated** - Each test should be independent
5. **Clear test names** - Describe what each test validates

## Future Enhancements

- [ ] Full Home Assistant test environment setup
- [ ] Integration tests with mocked HA components
- [ ] Configuration flow testing
- [ ] Entity state and attribute testing
- [ ] Filtration automation testing
- [ ] Performance and load testing

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Add docstrings explaining test purpose
3. Include both success and error scenarios
4. Update this README with new test counts
5. Ensure tests pass in CI/CD pipeline

For more detailed testing documentation, see [`docs/TESTING.md`](docs/TESTING.md).