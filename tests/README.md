# DevOps Universal Scanner - Test Suite

Comprehensive test suite for the DevOps Universal Scanner v3.0.

## Directory Structure

```
tests/
├── unit/                  # Unit tests (test individual components)
│   ├── test_pricing_aws.py
│   ├── test_pricing_azure.py
│   └── test_ami_cve_scanner.py
├── integration/           # Integration tests (test components working together)
│   └── test_scanner_integration.py
├── system/                # System tests (end-to-end scenarios)
│   └── (to be added)
└── manual/                # Manual/legacy test scripts
    ├── test_aws_pricing.py
    └── test_credential_detection.py
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-timeout

# Install the scanner package in development mode
pip install -e .
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=devops_universal_scanner --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# Specific test file
pytest tests/unit/test_pricing_aws.py

# Specific test class or function
pytest tests/unit/test_pricing_aws.py::TestAWSPricingAPIInitialization
pytest tests/unit/test_pricing_aws.py::TestAWSPricingAPIInitialization::test_initialization_with_boto3_available
```

### Run Tests by Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only tests that require network
pytest -m requires_network

# Exclude network tests
pytest -m "not requires_network"

# Run slow tests
pytest -m slow
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.system` - System tests for end-to-end scenarios
- `@pytest.mark.slow` - Tests that take a long time to run
- `@pytest.mark.requires_network` - Tests that require network access
- `@pytest.mark.requires_aws` - Tests that require AWS API access
- `@pytest.mark.requires_azure` - Tests that require Azure API access
- `@pytest.mark.requires_gcp` - Tests that require GCP API access

## Writing New Tests

### Unit Test Example

```python
"""
Unit tests for MyComponent
"""

import pytest
from devops_universal_scanner.core.my_component import MyComponent


class TestMyComponent:
    """Test MyComponent functionality"""

    @pytest.fixture
    def component(self):
        """Create component instance"""
        return MyComponent()

    def test_basic_functionality(self, component):
        """Test basic component functionality"""
        result = component.do_something()
        assert result is not None
        assert result["status"] == "success"

    @pytest.mark.slow
    def test_expensive_operation(self, component):
        """Test expensive operation"""
        result = component.expensive_operation()
        assert result is not None
```

### Integration Test Example

```python
"""
Integration tests for Scanner
"""

import pytest
from pathlib import Path
from devops_universal_scanner.core.scanner import Scanner


class TestScannerIntegration:
    """Test Scanner integration with real files"""

    @pytest.fixture
    def test_file(self):
        """Get test file path"""
        return Path("test-files/cloudformation/ec2-instance.yaml")

    def test_full_scan_workflow(self, test_file):
        """Test complete scanning workflow"""
        scanner = Scanner("cloudformation", test_file)
        exit_code = scanner.scan()
        assert isinstance(exit_code, int)
        assert scanner.log_file.exists()
```

## Test Coverage

View coverage report after running tests with coverage:

```bash
# Generate HTML coverage report
pytest --cov=devops_universal_scanner --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Continuous Integration

Tests are automatically run on:
- Every commit
- Every pull request
- Before merging to main branch

## Manual Test Scripts

The `manual/` directory contains legacy test scripts that can be run directly:

```bash
# Test AWS pricing API
python tests/manual/test_aws_pricing.py

# Test credential detection
python tests/manual/test_credential_detection.py
```

These are kept for backward compatibility and manual testing but are not part of the automated test suite.

## Best Practices

1. **Write tests first** (TDD approach recommended)
2. **Keep tests independent** - Each test should be able to run in isolation
3. **Use fixtures** for common setup code
4. **Mock external dependencies** in unit tests
5. **Use descriptive test names** - Test name should describe what is being tested
6. **Add docstrings** to test classes and functions
7. **Mark slow/network tests** appropriately
8. **Maintain high coverage** - Aim for >80% code coverage

## Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
# Install all dependencies including dev dependencies
pip install -r requirements.txt
```

### Tests Fail Due to Network Issues

```bash
# Skip network tests
pytest -m "not requires_network"
```

### Tests Fail Due to Import Errors

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH=/path/to/devops-universal-scanner

# Or install in development mode
pip install -e .
```

## Contributing

When adding new features:
1. Write tests for the new functionality
2. Ensure all existing tests still pass
3. Update this README if adding new test categories
4. Maintain or improve code coverage

---

**Last Updated**: 2025-11-19
**Test Framework**: pytest 8.0+
**Python Version**: 3.13+
