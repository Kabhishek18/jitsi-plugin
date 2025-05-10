# Run all tests
pytest

# Run specific test categories
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only

# Run with coverage report
pytest --cov=jitsi_py tests/
coverage html  # Generates HTML report in htmlcov/

# Run tests for multiple Python versions using tox
tox

# Run only a specific test file
pytest tests/unit/test_client.py

# Run a specific test function
pytest tests/unit/test_client.py::TestJitsiClient::test_create_room