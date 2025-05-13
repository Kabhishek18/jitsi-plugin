# tests/test_broadcast_controller.py (continued)
import pytest
import uuid
import time
from unittest.mock import Mock, patch, MagicMock, call

from jitsi_plus_plugin.features.broadcast import BroadcastController

@pytest.fixture
def mock_jitsi_connector():
    """Create a mock JitsiConnector."""
    mock = Mock()
    # Mock create_room method
    mock.create_room.return_value = {
        "room_name": "broadcast-12345678",
        "created_at": 1234567890,
        "features": {
            "video": True,
            "audio": True,
            "chat": True,
            "screen_sharing": True,
            "polls": True,
            "whiteboard": True,
            "settings": True,
            "background": True
        },
        "participants": {}
    }
    # Mock join_room method
    mock.join_room.return_value = {
        "id": "host-123",
        "name": "Test Host",
        "joined_at": 1234567890,
        "features": {
            "video": True,
            "audio": True,
            "screen_sharing": False
        }
    }
    # Mock get_jitsi_url method
    mock.get_jitsi_url.return_value = "https://test.jitsi.meet/broadcast-12345678"
    # Mock leave_room method
    mock.leave_room.return_value = True
    # Mock configure_room method
    mock.configure_room.return_value = True
    # Mock toggle_participant_feature method
    mock.toggle_participant_feature.return_value = True
    
    return mock

@pytest.fixture
def mock_media_server():
    """Create a mock MediaServer."""
    mock = Mock()
    # Mock create_stream method
    mock.create_stream.return_value = {
        "key": "stream-123",
        "rtmp_url": "rtmp://test.media.server:1935/live/stream-123",
        "hls_url": "https://test.media.server/hls/stream-123.m3u8",
        "status": "created",
        "created_at": 1234567890,
        "recording_path": "/tmp/recordings/stream-123.mp4"
    }
    # Mock start_stream method
    mock.start_stream.return_value = True
    # Mock stop_stream method
    mock.stop_stream.return_value = True
    # Mock list_vod_entries method
    mock.list_vod_entries.return_value = [
        {
            "id": "vod-stream-123",
            "name": "Test VOD",
            "source_stream": "stream-123",
            "url": "https://test.media.server/vod/vod-stream-123.mp4",
            "status": "ready"
        }
    ]
    
    return mock

@pytest.fixture
def mock_signaling_server():
    """Create a mock SignalingServer."""
    mock = Mock()
    return mock

@pytest.fixture
def broadcast_controller(mock_jitsi_connector, mock_media_server, mock_signaling_server):
    """Create a BroadcastController with mocked dependencies."""
    return BroadcastController(mock_jitsi_connector, mock_media_server, mock_signaling_server)

def test_create_broadcast(broadcast_controller, mock_jitsi_connector, mock_media_server):
    """Test creating a broadcast."""
    broadcast_name = "Test Broadcast"
    
    # Mock uuid.uuid4
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")), \
         patch('time.time', return_value=1234567890):
        
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Check that jitsi_connector.create_room was called
        mock_jitsi_connector.create_room.assert_called_once_with("broadcast-12345678-90ab-cdef-ghij-klmnopqrstuv")
        
        # Check that media_server.create_stream was called
        mock_media_server.create_stream.assert_called_once_with(
            f"{broadcast_name}-12345678-90ab-cdef-ghij-klmnopqrstuv", 
            "live_record"
        )
        
        # Check return value
        assert broadcast_info["id"] == "12345678-90ab-cdef-ghij-klmnopqrstuv"
        assert broadcast_info["name"] == broadcast_name
        assert broadcast_info["room_name"] == "broadcast-12345678"
        assert broadcast_info["jitsi_url"] == "https://test.jitsi.meet/broadcast-12345678"
        assert broadcast_info["stream_key"] == "stream-123"
        assert broadcast_info["rtmp_url"] == "rtmp://test.media.server:1935/live/stream-123"
        assert broadcast_info["hls_url"] == "https://test.media.server/hls/stream-123.m3u8"
        assert broadcast_info["created_at"] == 1234567890
        assert broadcast_info["features"]["video"] is True
        assert broadcast_info["features"]["audio"] is True
        assert broadcast_info["features"]["chat"] is True
        assert broadcast_info["max_hosts"] == 10
        assert broadcast_info["max_viewers"] == 10000
        assert broadcast_info["status"] == "created"
        assert broadcast_info["recording"] is False
        assert broadcast_info["hosts"] == {}
        assert broadcast_info["viewers"] == 0

def test_create_broadcast_with_config(broadcast_controller, mock_jitsi_connector):
    """Test creating a broadcast with custom configuration."""
    broadcast_name = "Test Broadcast"
    config = {
        "max_hosts": 3,
        "max_viewers": 5000,
        "features": {
            "whiteboard": False,
            "polls": True
        },
        "recording": True,
        "stream_type": "record"
    }
    
    # Mock uuid.uuid4
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name, config)
        
        # Check that jitsi_connector.configure_room was called with features
        mock_jitsi_connector.configure_room.assert_called_once_with("broadcast-12345678", config["features"])
        
        # Check return value
        assert broadcast_info["max_hosts"] == 3
        assert broadcast_info["max_viewers"] == 5000
        assert broadcast_info["recording"] is True

def test_start_broadcast(broadcast_controller, mock_media_server):
    """Test starting a broadcast."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast first
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")), \
         patch('time.time', return_value=1234567890):
        
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Now start the broadcast
        with patch('time.time', return_value=1234567895):
            result = broadcast_controller.start_broadcast(broadcast_info["id"])
            
            # Check that media_server.start_stream was called
            mock_media_server.start_stream.assert_called_once_with("stream-123")
            
            # Check result
            assert result is True
            
            # Check that broadcast status and start time were updated
            assert broadcast_info["status"] == "live"
            assert broadcast_info["started_at"] == 1234567895

def test_stop_broadcast(broadcast_controller, mock_media_server):
    """Test stopping a broadcast."""
    broadcast_name = "Test Broadcast"
    
    # Create and start a broadcast
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")), \
         patch('time.time', side_effect=[1234567890, 1234567895, 1234567900]):
        
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        broadcast_controller.start_broadcast(broadcast_info["id"])
        
        # Now stop the broadcast
        result = broadcast_controller.stop_broadcast(broadcast_info["id"])
        
        # Check that media_server.stop_stream was called
        mock_media_server.stop_stream.assert_called_once_with("stream-123")
        
        # Check result
        assert result is True
        
        # Check that broadcast status and end time were updated
        assert broadcast_info["status"] == "ended"
        assert broadcast_info["ended_at"] == 1234567900

def test_add_host(broadcast_controller, mock_jitsi_connector):
    """Test adding a host to a broadcast."""
    broadcast_name = "Test Broadcast"
    host_name = "Test Host"
    
    # Create a broadcast first
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Now add a host
        host_info = broadcast_controller.add_host(broadcast_info["id"], host_name)
        
        # Check that jitsi_connector.join_room was called
        mock_jitsi_connector.join_room.assert_called_once_with(broadcast_info["room_name"], host_name)
        
        # Check return value
        assert host_info["id"] == "host-123"
        assert host_info["name"] == "Test Host"
        assert host_info["features"]["video"] is True
        assert host_info["features"]["audio"] is True
        
        # Check that host was added to the broadcast
        assert "host-123" in broadcast_info["hosts"]
        assert broadcast_info["hosts"]["host-123"] == host_info

def test_add_host_with_config(broadcast_controller, mock_jitsi_connector):
    """Test adding a host to a broadcast with custom configuration."""
    broadcast_name = "Test Broadcast"
    host_name = "Test Host"
    
    # Create a broadcast first
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Now add a host with custom config
        host_config = {
            "features": {
                "video": False,
                "screen_sharing": True
            }
        }
        
        host_info = broadcast_controller.add_host(broadcast_info["id"], host_name, host_config)
        
        # Check that jitsi_connector.toggle_participant_feature was called twice
        assert mock_jitsi_connector.toggle_participant_feature.call_count == 2
        
        # Check calls to toggle_participant_feature
        calls = mock_jitsi_connector.toggle_participant_feature.call_args_list
        assert calls[0][0] == (broadcast_info["room_name"], "host-123", "video", False)
        assert calls[1][0] == (broadcast_info["room_name"], "host-123", "screen_sharing", True)

def test_add_host_max_reached(broadcast_controller):
    """Test adding a host when the maximum number is reached."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast with max_hosts=1
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name, {"max_hosts": 1})
        
        # Add the first host
        host_info = broadcast_controller.add_host(broadcast_info["id"], "First Host")
        assert host_info is not None
        
        # Try to add another host
        with pytest.raises(ValueError, match=f"Broadcast has reached maximum number of hosts: {broadcast_info['id']}"):
            broadcast_controller.add_host(broadcast_info["id"], "Second Host")

def test_remove_host(broadcast_controller, mock_jitsi_connector):
    """Test removing a host from a broadcast."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast and add a host
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        host_info = broadcast_controller.add_host(broadcast_info["id"], "Test Host")
        
        # Now remove the host
        result = broadcast_controller.remove_host(broadcast_info["id"], host_info["id"])
        
        # Check that jitsi_connector.leave_room was called
        mock_jitsi_connector.leave_room.assert_called_once_with(broadcast_info["room_name"], host_info["id"])
        
        # Check result
        assert result is True
        
        # Check that host was removed from the broadcast
        assert host_info["id"] not in broadcast_info["hosts"]

def test_get_broadcast_info(broadcast_controller):
    """Test getting broadcast information."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Get broadcast info
        retrieved_info = broadcast_controller.get_broadcast_info(broadcast_info["id"])
        
        # Check that we got the same info back
        assert retrieved_info is broadcast_info
        assert retrieved_info["id"] == "12345678-90ab-cdef-ghij-klmnopqrstuv"
        assert retrieved_info["name"] == broadcast_name

def test_list_active_broadcasts(broadcast_controller):
    """Test listing active broadcasts."""
    # Create a couple of broadcasts
    with patch('uuid.uuid4', side_effect=[
        Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv"),
        Mock(spec=uuid.UUID, __str__=lambda _: "87654321-abcd-efgh-ijkl-mnopqrstuvw")
    ]):
        broadcast1 = broadcast_controller.create_broadcast("Broadcast 1")
        broadcast2 = broadcast_controller.create_broadcast("Broadcast 2")
        
        # Set status of first broadcast to "live"
        broadcast1["status"] = "live"
        
        # List active broadcasts
        active_broadcasts = broadcast_controller.list_active_broadcasts()
        
        # Check that only the live broadcast is in the list
        assert len(active_broadcasts) == 1
        assert broadcast1 in active_broadcasts
        assert broadcast2 not in active_broadcasts

def test_toggle_broadcast_feature(broadcast_controller, mock_jitsi_connector):
    """Test toggling a broadcast feature."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Toggle a feature
        result = broadcast_controller.toggle_broadcast_feature(broadcast_info["id"], "video", False)
        
        # Check that jitsi_connector.configure_room was called
        mock_jitsi_connector.configure_room.assert_called_with(broadcast_info["room_name"], {"video": False})
        
        # Check result
        assert result is True
        
        # Check that the feature was updated in the broadcast info
        assert broadcast_info["features"]["video"] is False

def test_toggle_host_feature(broadcast_controller, mock_jitsi_connector):
    """Test toggling a host feature."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast and add a host
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        host_info = broadcast_controller.add_host(broadcast_info["id"], "Test Host")
        
        # Toggle a feature
        result = broadcast_controller.toggle_host_feature(
            broadcast_info["id"], host_info["id"], "screen_sharing", True
        )
        
        # Check that jitsi_connector.toggle_participant_feature was called
        mock_jitsi_connector.toggle_participant_feature.assert_called_with(
            broadcast_info["room_name"], host_info["id"], "screen_sharing", True
        )
        
        # Check result
        assert result is True
        
        # Check that the feature was updated in the host info
        assert broadcast_info["hosts"][host_info["id"]]["features"]["screen_sharing"] is True

def test_update_viewer_count(broadcast_controller):
    """Test updating viewer count."""
    broadcast_name = "Test Broadcast"
    
    # Create a broadcast
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name)
        
        # Update viewer count
        result = broadcast_controller.update_viewer_count(broadcast_info["id"], 5000)
        
        # Check result
        assert result is True
        
        # Check that viewer count was updated
        assert broadcast_info["viewers"] == 5000

def test_get_recording_url(broadcast_controller, mock_media_server):
    """Test getting recording URL."""
    broadcast_name = "Test Broadcast"
    
    # Create, start, and stop a broadcast
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name, {"recording": True})
        broadcast_controller.start_broadcast(broadcast_info["id"])
        broadcast_controller.stop_broadcast(broadcast_info["id"])
        
        # Get recording URL
        recording_url = broadcast_controller.get_recording_url(broadcast_info["id"])
        
        # Check that list_vod_entries was called
        mock_media_server.list_vod_entries.assert_called_once()
        
        # Check result
        assert recording_url == "https://test.media.server/vod/vod-stream-123.mp4"

def test_get_recording_url_none(broadcast_controller, mock_media_server):
    """Test getting recording URL when there's no recording."""
    broadcast_name = "Test Broadcast"
    
    # Create and start a broadcast, but not stopped yet
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        broadcast_info = broadcast_controller.create_broadcast(broadcast_name, {"recording": True})
        broadcast_controller.start_broadcast(broadcast_info["id"])
        
        # Get recording URL
        recording_url = broadcast_controller.get_recording_url(broadcast_info["id"])
        
        # Check result
        assert recording_url is None