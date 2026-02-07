# Unit Tests for Leneda Integration

This directory contains comprehensive unit tests for the Leneda Home Assistant integration.

## Test Coverage

- **test_init.py**: Tests for integration setup and teardown
- **test_config_flow.py**: Tests for configuration flow and user input validation
- **test_const.py**: Tests for constants and OBIS code mappings
- **test_sensor.py**: Tests for sensor entities and API interactions

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_sensor.py
```

### Run Specific Test

```bash
pytest tests/test_sensor.py::test_metering_sensor_initialization
```

### Run with Coverage Report

```bash
pytest --cov=custom_components/leneda --cov-report=html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Async Tests Only

```bash
pytest -m asyncio
```

## Test Structure

Each test file follows this pattern:

1. **Fixtures**: Mock objects and test data setup
2. **Unit Tests**: Individual test functions for specific functionality
3. **Assertions**: Verification of expected behavior

## Mocking Strategy

The tests use `unittest.mock` to mock:

- Home Assistant core components
- Configuration entries
- HTTP sessions and API responses
- Database recorder operations

## Key Test Areas

### Initialization Tests
- Verify domain setup and platform initialization
- Test configuration entry creation and removal

### Configuration Flow Tests
- Validate user input handling
- Test unique ID generation
- Verify form schema and defaults

### Constant Tests
- Verify all constants are properly defined
- Test OBIS code mappings
- Validate default values

### Sensor Tests
- Test sensor initialization with different OBIS codes
- Mock API interactions and responses
- Verify data transformation and aggregation
- Test polling and update mechanisms

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention: `test_<functionality>`
2. Use descriptive docstrings
3. Create appropriate fixtures for test data
4. Mock external dependencies
5. Use assertions to verify expected behavior

Example:

```python
@pytest.mark.asyncio
async def test_new_feature(mock_hass, mock_config):
    """Test description."""
    # Setup
    entity = LenedaMeteringSensor(mock_hass, mock_config)
    
    # Execute
    result = await entity.async_update()
    
    # Assert
    assert result is not None
```
