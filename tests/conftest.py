# tests/conftest.py

import pytest
import os
import json
from unittest.mock import MagicMock
import requests_mock

from jitsi_py.core.client import JitsiClient, JitsiServerConfig, JitsiServerType
from jitsi_py.api.rest import JitsiRestClient

@pytest.fixture
def mock_rest_api():
    """Fixture to mock REST API calls."""
    with requests_mock.Mocker() as m:
        yield m

@pytest.fixture
def jitsi_client():
    """Fixture to create a JitsiClient instance."""
    server_config = JitsiServerConfig(
        server_type=JitsiServerType.PUBLIC,
        domain="meet.jit.si"
    )
    
    return JitsiClient(
        server_config=server_config,
        app_id="test_app",
        jwt_secret="test_secret"
    )

@pytest.fixture
def jitsi_rest_client():
    """Fixture to create a JitsiRestClient instance."""
    return JitsiRestClient(
        api_endpoint="https://api.jitsi.example.com",
        api_key="test_api_key"
    )

@pytest.fixture
def sample_room_config():
    """Fixture with sample room configuration."""
    return {
        "name": "test-room",
        "features": {
            "audio": {
                "enabled": True,
                "muted": False
            },
            "video": {
                "enabled": True,
                "muted": False
            }
        },
        "expiry": 3600
    }

@pytest.fixture
def mock_websocket():
    """Fixture to mock WebSocket connections."""
    mock = MagicMock()
    mock.run_forever = MagicMock()
    mock.send = MagicMock()
    mock.close = MagicMock()
    
    return mock

@pytest.fixture
def load_mock_data():
    """Fixture to load mock data from files."""
    def _load_data(filename):
        path = os.path.join(os.path.dirname(__file__), "mocks", filename)
        with open(path, "r") as f:
            return json.load(f)
    
    return _load_data