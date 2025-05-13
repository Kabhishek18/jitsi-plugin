# tests/test_media_server_vod.py
import pytest
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
import time

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
    with patch('os.makedirs') as mock_makedirs:
        server = MediaServer(media_server_config)
        # Mock initialization since we're only testing VOD functionality
        server.connected = True
        return server

def test_create_vod_entry(media_server):
    """Test creating a VOD entry from a file."""
    vod_name = "test_vod"
    file_path = "/tmp/test_video.mp4"
    
    # Mock file existence check
    with patch('os.path.exists', return_value=True), \
         patch('threading.Thread') as mock_thread, \
         patch('time.time', return_value=1234567890):
        
        vod_info = media_server.create_vod_entry(vod_name, file_path)
        
        # Check returned VOD info
        assert vod_info["id"].startswith("vod-")
        assert vod_info["name"] == vod_name
        assert vod_info["source_stream"] is None
        assert vod_info["created_at"] == 1234567890
        assert vod_info["file_path"] == file_path
        assert vod_info["url"] == f"https://media.example.com/vod/{vod_info['id']}.mp4"
        assert vod_info["status"] == "processing"
        
        # Check that VOD entry was added
        assert vod_info["id"] in media_server.vod_entries
        
        # Check that processing thread was started
        mock_thread.assert_called_once()
        assert mock_thread.call_args[1]["target"] == media_server._process_vod_file
        assert mock_thread.call_args[1]["args"] == (vod_info["id"], file_path)
        assert mock_thread.return_value.start.call_count == 1

def test_create_vod_entry_file_not_found(media_server):
    """Test creating a VOD entry with a file that doesn't exist."""
    vod_name = "test_vod"
    file_path = "/tmp/nonexistent_video.mp4"
    
    # Mock file existence check
    with patch('os.path.exists', return_value=False):
        with pytest.raises(FileNotFoundError, match=f"VOD file not found: {file_path}"):
            media_server.create_vod_entry(vod_name, file_path)

def test_process_vod_file(media_server):
    """Test processing a VOD file."""
    vod_id = "vod-test"
    file_path = "/tmp/test_video.mp4"
    
    # Create a VOD entry
    media_server.vod_entries[vod_id] = {
        "id": vod_id,
        "name": "Test VOD",
        "source_stream": None,
        "created_at": time.time(),
        "duration": None,
        "file_path": file_path,
        "url": f"https://media.example.com/vod/{vod_id}.mp4",
        "status": "processing"
    }
    
    # Mock subprocess.run to return duration
    mock_result = Mock()
    mock_result.stdout = "123.45\n"
    
    with patch('subprocess.run', return_value=mock_result) as mock_run, \
         patch('os.path.dirname', return_value="/tmp"), \
         patch('os.path.basename', return_value=f"{vod_id}_thumbnail.jpg"):
        
        # Call the method directly
        media_server._process_vod_file(vod_id, file_path)
        
        # Check FFprobe call to get duration
        assert mock_run.call_count == 2
        ffprobe_args = mock_run.call_args_list[0][0][0]
        assert ffprobe_args[0] == "ffprobe"
        assert file_path in ffprobe_args
        
        # Check FFmpeg call to generate thumbnail
        ffmpeg_args = mock_run.call_args_list[1][0][0]
        assert ffmpeg_args[0] == "ffmpeg"
        assert file_path in ffmpeg_args
        assert "thumbnail.jpg" in ffmpeg_args[-1]
        
        # Check that VOD entry was updated
        assert media_server.vod_entries[vod_id]["duration"] == 123.45
        assert media_server.vod_entries[vod_id]["status"] == "ready"
        assert "thumbnail_url" in media_server.vod_entries[vod_id]

def test_process_vod_file_error(media_server):
    """Test processing a VOD file with an error."""
    vod_id = "vod-test"
    file_path = "/tmp/test_video.mp4"
    
    # Create a VOD entry
    media_server.vod_entries[vod_id] = {
        "id": vod_id,
        "name": "Test VOD",
        "source_stream": None,
        "created_at": time.time(),
        "duration": None,
        "file_path": file_path,
        "url": f"https://media.example.com/vod/{vod_id}.mp4",
        "status": "processing"
    }
    
    # Mock subprocess.run to raise an exception
    with patch('subprocess.run', side_effect=Exception("Test error")):
        
        # Call the method directly
        media_server._process_vod_file(vod_id, file_path)
        
        # Check that VOD entry status was updated to error
        assert media_server.vod_entries[vod_id]["status"] == "error"

def test_get_vod_info(media_server):
    """Test getting VOD information."""
    vod_id = "vod-test"
    
    # Create a VOD entry
    vod_info = {
        "id": vod_id,
        "name": "Test VOD",
        "source_stream": None,
        "created_at": time.time(),
        "duration": 123.45,
        "file_path": "/tmp/test_video.mp4",
        "url": f"https://media.example.com/vod/{vod_id}.mp4",
        "status": "ready"
    }
    media_server.vod_entries[vod_id] = vod_info
    
    # Get VOD info
    retrieved_info = media_server.get_vod_info(vod_id)
    
    # Check that we got the same info back
    assert retrieved_info is vod_info

def test_list_vod_entries(media_server):
    """Test listing VOD entries."""
    # Create a few VOD entries
    vod1 = {
        "id": "vod-1",
        "name": "VOD 1",
        "status": "ready"
    }
    vod2 = {
        "id": "vod-2",
        "name": "VOD 2",
        "status": "processing"
    }
    vod3 = {
        "id": "vod-3",
        "name": "VOD 3",
        "status": "error"
    }
    
    media_server.vod_entries = {
        "vod-1": vod1,
        "vod-2": vod2,
        "vod-3": vod3
    }
    
    # List VOD entries
    vod_entries = media_server.list_vod_entries()
    
    # Check that all entries are in the list
    assert len(vod_entries) == 3
    assert vod1 in vod_entries
    assert vod2 in vod_entries
    assert vod3 in vod_entries

def test_configure_ad_settings(media_server):
    """Test configuring advertisement settings for a VOD entry."""
    vod_id = "vod-test"
    
    # Create a VOD entry
    vod_info = {
        "id": vod_id,
        "name": "Test VOD",
        "status": "ready"
    }
    media_server.vod_entries[vod_id] = vod_info
    
    # Configure ad settings
    ad_config = {
        "pre_roll": ["https://example.com/ads/pre_roll.mp4"],
        "mid_roll": [
            {"time": 30, "url": "https://example.com/ads/mid_roll1.mp4"},
            {"time": 60, "url": "https://example.com/ads/mid_roll2.mp4"}
        ],
        "post_roll": ["https://example.com/ads/post_roll.mp4"]
    }
    
    result = media_server.configure_ad_settings(vod_id, ad_config)
    
    # Check result
    assert result is True
    
    # Check that ad configuration was added to VOD entry
    assert "ad_config" in vod_info
    assert vod_info["ad_config"]["pre_roll"] == ad_config["pre_roll"]
    assert vod_info["ad_config"]["mid_roll"] == ad_config["mid_roll"]
    assert vod_info["ad_config"]["post_roll"] == ad_config["post_roll"]

def test_delete_vod_entry(media_server):
    """Test deleting a VOD entry."""
    vod_id = "vod-test"
    file_path = "/tmp/test_video.mp4"
    
    # Create a VOD entry
    vod_info = {
        "id": vod_id,
        "name": "Test VOD",
        "file_path": file_path,
        "status": "ready"
    }
    media_server.vod_entries[vod_id] = vod_info
    
    # Delete VOD entry without deleting the file
    with patch('os.path.exists', return_value=True):
        result = media_server.delete_vod_entry(vod_id, delete_file=False)
        
        # Check result
        assert result is True
        
        # Check that VOD entry was removed
        assert vod_id not in media_server.vod_entries

def test_delete_vod_entry_with_file(media_server):
    """Test deleting a VOD entry including the file."""
    vod_id = "vod-test"
    file_path = "/tmp/test_video.mp4"
    
    # Create a VOD entry
    vod_info = {
        "id": vod_id,
        "name": "Test VOD",
        "file_path": file_path,
        "status": "ready"
    }
    media_server.vod_entries[vod_id] = vod_info
    
    # Delete VOD entry with file deletion
    with patch('os.path.exists', return_value=True), \
         patch('os.remove') as mock_remove:
        
        result = media_server.delete_vod_entry(vod_id, delete_file=True)
        
        # Check result
        assert result is True
        
        # Check that VOD entry was removed
        assert vod_id not in media_server.vod_entries
        
        # Check that file was deleted
        mock_remove.assert_called_once_with(file_path)

def test_stop_recording(media_server):
    """Test stopping a recording."""
    stream_key = "test-stream"
    
    # Create a mock process
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.return_value = 0
    
    # Add it to recording processes
    media_server.recording_processes[stream_key] = mock_process
    
    # Set up a callback
    mock_callback = Mock()
    media_server.on_recording_completed = mock_callback
    
    # Add a stream info
    media_server.active_streams[stream_key] = {"name": "Test Stream"}
    
    # Stop the recording
    media_server._stop_recording(stream_key)
    
    # Check that process.terminate was called
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    
    # Check that recording process was removed
    assert stream_key not in media_server.recording_processes
    
    # Check that callback was called
    mock_callback.assert_called_once_with({"name": "Test Stream"})

def test_stop_recording_force_kill(media_server):
    """Test stopping a recording with force kill."""
    stream_key = "test-stream"
    
    # Create a mock process that doesn't terminate gracefully
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired("ffmpeg", 5)
    
    # Add it to recording processes
    media_server.recording_processes[stream_key] = mock_process
    
    # Stop the recording
    media_server._stop_recording(stream_key)
    
    # Check that process.kill was called after terminate
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    mock_process.kill.assert_called_once()

def test_shutdown(media_server):
    """Test shutting down the media server."""
    # Create some active streams and recordings
    stream_key1 = "stream1"
    stream_key2 = "stream2"
    
    media_server.active_streams = {
        stream_key1: {"status": "active", "name": "Stream 1"},
        stream_key2: {"status": "active", "name": "Stream 2"}
    }
    
    # Add a recording process
    mock_process = Mock()
    media_server.recording_processes[stream_key1] = mock_process
    
    # Mock stop_recording and stop_stream methods
    with patch.object(media_server, '_stop_recording') as mock_stop_recording, \
         patch.object(media_server, 'stop_stream') as mock_stop_stream:
        
        # Shutdown the media server
        media_server.shutdown()
        
        # Check that all recordings were stopped
        mock_stop_recording.assert_called_once_with(stream_key1)
        
        # Check that all active streams were stopped
        assert mock_stop_stream.call_count == 2
        mock_stop_stream.assert_has_calls([
            call(stream_key1),
            call(stream_key2)
        ], any_order=True)