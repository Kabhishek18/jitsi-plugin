# tests/unit/test_url_builder.py

import pytest
from urllib.parse import urlparse, parse_qs

from jitsi_py.utils.url import build_jitsi_url, _convert_features_to_params

class TestUrlBuilder:
    
    def test_build_basic_url(self):
        """Test building a basic Jitsi URL."""
        url = build_jitsi_url(
            domain="meet.jit.si",
            room_name="test-room"
        )
        
        assert url == "https://meet.jit.si/test-room"
    
    def test_build_url_with_protocol(self):
        """Test building a URL with protocol in domain."""
        url = build_jitsi_url(
            domain="https://meet.jit.si",
            room_name="test-room"
        )
        
        assert url == "https://meet.jit.si/test-room"
    
    def test_build_url_with_token(self):
        """Test building a URL with JWT token."""
        url = build_jitsi_url(
            domain="meet.jit.si",
            room_name="test-room",
            token="test_jwt_token"
        )
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.fragment)
        
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc == "meet.jit.si"
        assert parsed_url.path == "/test-room"
        assert query_params["jwt"] == ["test_jwt_token"]
    
    def test_build_url_with_features(self):
        """Test building a URL with features."""
        features = {
            "audio": {
                "muted": True,
                "enabled": False
            },
            "video": {
                "muted": True
            },
            "streaming": {
                "enabled": True
            },
            "ui": {
                "hide_buttons": ["settings", "invite"]
            }
        }
        
        url = build_jitsi_url(
            domain="meet.jit.si",
            room_name="test-room",
            features=features
        )
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.fragment)
        
        assert "config.startWithAudioMuted" in query_params
        assert query_params["config.startWithAudioMuted"] == ["true"]
        assert "config.disableAudioLevels" in query_params
        assert query_params["config.disableAudioLevels"] == ["true"]
        assert "config.startWithVideoMuted" in query_params
        assert query_params["config.startWithVideoMuted"] == ["true"]
        assert "config.enableLiveStreaming" in query_params
        assert query_params["config.enableLiveStreaming"] == ["true"]
        assert "config.toolbarButtons" in query_params
    
    def test_convert_features_to_params(self):
        """Test converting feature configs to URL parameters."""
        features = {
            "audio": {
                "muted": True,
                "enabled": False
            },
            "video": {
                "muted": True,
                "enabled": True
            },
            "streaming": {
                "enabled": True
            },
            "recording": {
                "enabled": True
            },
            "room": {
                "protected": True,
                "password": "test123",
                "lobby_enabled": True
            }
        }
        
        params = _convert_features_to_params(features)
        
        assert params["config.startWithAudioMuted"] == "true"
        assert params["config.disableAudioLevels"] == "true"
        assert params["config.startWithVideoMuted"] == "true"
        assert params["config.enableLiveStreaming"] == "true"
        assert params["config.enableRecording"] == "true"
        assert params["config.requirePassword"] == "true"
        assert params["config.password"] == "test123"
        assert params["config.enableLobby"] == "true"