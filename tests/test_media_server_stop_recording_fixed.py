# tests/test_media_server_stop_recording_fixed.py
import pytest
import subprocess
from unittest.mock import Mock, patch

from jitsi_plus_plugin.core.media_server import MediaServer

@pytest.fixture
def media_server_config():
    """Create a test configuration for MediaServer."""
    return {
        "server_url": "https://media.example.com",
        "rtmp_port": 1935,
        "hls_segment_duration": 4,
        "recording_enabled": True,
        "recording_directory": "/tmp/recordings"
    }

@pytest.fixture
def media_server(media_server_config):
    """Create a MediaServer instance with test configuration."""
    with patch('os.makedirs'):
        server = MediaServer(media_server_config)
        return server

def test_stop_recording_force_kill_fixed(media_server):
    """Test stopping a recording with force kill."""
    stream_key = "test-stream"
    
    # Create a mock process that doesn't terminate gracefully
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired("ffmpeg", 5)
    mock_process.kill = Mock()  # Add explicit mock for kill method
    
    # Add it to recording processes
    media_server.recording_processes[stream_key] = mock_process
    
    # Add stream info for callback
    media_server.active_streams[stream_key] = {"name": "Test Stream"}
    
    # Stop the recording
    media_server._stop_recording(stream_key)
    
    # Check that process.kill was called after terminate
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    mock_process.kill.assert_called_once()