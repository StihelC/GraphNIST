# GraphNIST Testing Guide

This directory contains tests for the GraphNIST application. The tests are designed to verify that the application works correctly and to catch regressions when changes are made.

## Testing Framework

We use pytest as our testing framework along with the pytest-qt plugin for testing PyQt-based GUI components. The tests are organized as follows:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **UI Tests**: Test the user interface components

## Directory Structure

```
tests/
├── conftest.py          # Common fixtures and setup for tests
├── unit/                # Unit tests
│   ├── test_connection_controller.py
│   ├── test_layout_optimization.py
│   └── test_layout_optimization_dialog.py
└── README.md            # This file
```

## Running Tests

To run the tests, use the `run_tests.py` script in the root directory:

```bash
# Activate the virtual environment first
.\.venv\Scripts\activate

# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py unit
```

Alternatively, you can run pytest directly:

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run a specific test file
pytest tests/unit/test_connection_controller.py

# Run a specific test
pytest tests/unit/test_connection_controller.py::TestConnectionController::test_connection_exists_both_directions
```

## Writing New Tests

### Creating a New Test File

1. Create a new Python file in the appropriate directory (e.g., `tests/unit/`)
2. Name it `test_*.py` to be recognized by pytest
3. Import the necessary modules and create a test class

```python
import pytest
from unittest.mock import MagicMock, patch

from module.to.test import ClassToTest

class TestMyClass:
    """Test suite for MyClass."""
    
    @pytest.mark.unit  # Mark as a unit test
    def test_some_functionality(self):
        """Test description."""
        # Setup
        instance = ClassToTest()
        
        # Execute
        result = instance.method_to_test()
        
        # Assert
        assert result == expected_value
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in tests as function parameters:

```python
def test_with_fixtures(mock_canvas, mock_event_bus):
    """Test using fixtures."""
    controller = ConnectionController(mock_canvas, mock_event_bus)
    # Test implementation
```

### Mocking Dependencies

Use the unittest.mock library to mock dependencies:

```python
@patch('module.to.patch.ClassName')
def test_with_patching(mock_class):
    """Test using patching."""
    mock_class.return_value.method.return_value = 'mocked value'
    # Test implementation
```

## Test Coverage

To measure test coverage, install the pytest-cov plugin:

```bash
pip install pytest-cov
```

Then run pytest with coverage:

```bash
pytest --cov=src
```

## Troubleshooting

If you encounter any issues running the tests:

1. Make sure the virtual environment is activated
2. Check that all dependencies are installed
3. Verify that the import paths are correct
4. Look for any errors in the test output

## Best Practices

1. **Write tests first**: Consider test-driven development (TDD) when adding new features
2. **Keep tests independent**: Each test should be able to run independently from others
3. **Mock external dependencies**: Use mocking to isolate the code being tested
4. **Clear test names**: Use descriptive test names that explain what is being tested
5. **Document tests**: Add comments explaining complex test logic
6. **Test edge cases**: Consider corner cases and error conditions 