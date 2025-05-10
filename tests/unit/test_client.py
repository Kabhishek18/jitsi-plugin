# tests/unit/test_client.py

import pytest
from unittest.mock import patch, MagicMock

from jitsi_py.core.client import JitsiClient, JitsiServerConfig, JitsiServerType
from jitsi_py.core.room import Room

class TestJitsiClient:
    
    def test_init_default_config(self):
        """Test client initialization with default config."""
        client = JitsiClient()
        
        assert client.server_config.server_type == JitsiServerType.PUBLIC
        assert client.server_config.domain == "meet.jit.si"
        assert client.server_config.secure is True
        assert client.app_id is None
        assert client.api_key is None
        assert client.jwt_secret is None
    
    def test_init_custom_config(self):
        """Test client initialization with custom config."""
        server_config = JitsiServerConfig(
            server_type=JitsiServerType.SELF_HOSTED,
            domain="custom.jitsi.example.com",
            secure=True,
            api_endpoint="https://api.example.com/jitsi"
        )
        
        client = JitsiClient(
            server_config=server_config,
            app_id="test_app",
            api_key="test_api_key",
            jwt_secret="test_jwt_secret"
        )
        
        assert client.server_config.server_type == JitsiServerType.SELF_HOSTED
        assert client.server_config.domain == "custom.jitsi.example.com"
        assert client.server_config.secure is True
        assert client.server_config.api_endpoint == "https://api.example.com/jitsi"
        assert client.app_id == "test_app"
        assert client.api_key == "test_api_key"
        assert client.jwt_secret == "test_jwt_secret"
    
    def test_create_room(self, jitsi_client):
        """Test room creation."""
        room = jitsi_client.create_room("test-room", {"audio": {"enabled": True}}, 3600)
        
        assert isinstance(room, Room)
        assert room.state.name == "test-room"
        assert room.state.features == {"audio": {"enabled": True}}
        assert room.state.expiry == 3600
    
    def test_get_room(self, jitsi_client):
        """Test getting an existing room."""
        room = jitsi_client.get_room("existing-room")
        
        assert isinstance(room, Room)
        assert room.state.name == "existing-room"
    
    @patch("jitsi_py.security.tokens.generate_jwt_token")
    @patch("jitsi_py.utils.url.build_jitsi_url")
    def test_generate_room_url_with_jwt(self, mock_build_url, mock_generate_token, jitsi_client):
        """Test generating a room URL with JWT authentication."""
        mock_generate_token.return_value = "test_jwt_token"
        mock_build_url.return_value = "https://meet.jit.si/test-room#jwt=test_jwt_token"
        
        url = jitsi_client.generate_room_url(
            room_name="test-room",
            user_name="Test User",
            user_email="test@example.com",
            role="host"
        )
        
        mock_generate_token.assert_called_once()
        mock_build_url.assert_called_once()
        assert url == "https://meet.jit.si/test-room#jwt=test_jwt_token"
    
    @patch("jitsi_py.utils.url.build_jitsi_url")
    def test_generate_room_url_without_jwt(self, mock_build_url, jitsi_client):
        """Test generating a room URL without JWT authentication."""
        # Remove JWT secret to test without JWT
        jitsi_client.jwt_secret = None
        
        mock_build_url.return_value = "https://meet.jit.si/test-room"
        
        url = jitsi_client.generate_room_url(
            room_name="test-room",
            user_name="Test User",
            features={"audio": {"muted": True}}
        )
        
        mock_build_url.assert_called_once()
        assert url == "https://meet.jit.si/test-room"