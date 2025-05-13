# tests/test_jitsi_plus_plugin.py
import pytest
from unittest.mock import Mock, patch

from jitsi_plus_plugin import JitsiPlusPlugin
from jitsi_plus_plugin.core.jitsi_connector import JitsiConnector
from jitsi_plus_plugin.core.media_server import MediaServer
from jitsi_plus_plugin.core.signaling import SignalingServer

@pytest.fixture
def mock_jitsi_connector():
    """Create a mock JitsiConnector."""
    mock = Mock(spec=JitsiConnector)
    mock.initialize.return_value = True
    mock.disconnect.return_value = None
    return mock

@pytest.fixture
def mock_media_server():
    """Create a mock MediaServer."""
    mock = Mock(spec=MediaServer)
    mock.initialize.return_value = True
    mock.shutdown.return_value = None
    return mock

@pytest.fixture
def mock_signaling_server():
    """Create a mock SignalingServer."""
    mock = Mock(spec=SignalingServer)
    mock.start.return_value = True
    mock.stop.return_value = True
    return mock

@pytest.fixture
def plugin(mock_jitsi_connector, mock_media_server, mock_signaling_server):
    """Create a JitsiPlusPlugin with mocked dependencies."""
    with patch('jitsi_plus_plugin.JitsiConnector', return_value=mock_jitsi_connector), \
         patch('jitsi_plus_plugin.MediaServer', return_value=mock_media_server), \
         patch('jitsi_plus_plugin.SignalingServer', return_value=mock_signaling_server):
        plugin = JitsiPlusPlugin()
        return plugin

def test_initialize(plugin, mock_jitsi_connector, mock_media_server, mock_signaling_server):
    """Test the initialize method of JitsiPlusPlugin."""
    result = plugin.initialize()
    
    # Check that all core components were initialized
    mock_jitsi_connector.initialize.assert_called_once()
    mock_media_server.initialize.assert_called_once()
    mock_signaling_server.start.assert_called_once()
    
    # Check return value
    assert result["status"] == "initialized"
    assert "version" in result
    assert "features" in result
    assert result["features"]["video_call"] is True
    assert result["features"]["audio_call"] is True
    assert result["features"]["broadcast"] is True
    assert result["features"]["vod"] is True
    assert result["features"]["whiteboard"] is True
    assert result["features"]["polls"] is True

def test_shutdown(plugin, mock_jitsi_connector, mock_media_server, mock_signaling_server):
    """Test the shutdown method of JitsiPlusPlugin."""
    result = plugin.shutdown()
    
    # Check that all core components were shut down
    mock_signaling_server.stop.assert_called_once()
    mock_media_server.shutdown.assert_called_once()
    mock_jitsi_connector.disconnect.assert_called_once()
    
    # Check return value
    assert result["status"] == "shutdown"

def test_plugin_with_config():
    """Test creating JitsiPlusPlugin with custom configuration."""
    config = {
        "jitsi": {
            "server_url": "https://custom.jitsi.meet",
            "room_prefix": "custom-"
        },
        "media_server": {
            "server_url": "https://media.example.org",
            "rtmp_port": 1936
        },
        "signaling": {
            "host": "127.0.0.1",
            "port": 8081
        }
    }
    
    with patch('jitsi_plus_plugin.JitsiConnector') as mock_jitsi_cls, \
         patch('jitsi_plus_plugin.MediaServer') as mock_media_cls, \
         patch('jitsi_plus_plugin.SignalingServer') as mock_signaling_cls:
        
        plugin = JitsiPlusPlugin(config)
        
        # Check that the configuration was passed to the components
        mock_jitsi_cls.assert_called_once_with(config.get("jitsi", {}))
        mock_media_cls.assert_called_once_with(config.get("media_server", {}))
        mock_signaling_cls.assert_called_once_with(config.get("signaling", {}))