# tests/test_jitsi_connector.py
import pytest
import uuid
import json
from unittest.mock import Mock, patch, AsyncMock

from jitsi_plus_plugin.core.jitsi_connector import JitsiConnector

@pytest.fixture
def jitsi_connector():
    """Create a JitsiConnector instance with test configuration."""
    config = {
        "server_url": "https://test.jitsi.meet",
        "room_prefix": "test-",
        "use_ssl": True
    }
    return JitsiConnector(config)

@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {"status": "success"}
    return mock

def test_initialize(jitsi_connector, mock_response):
    """Test the initialize method."""
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = jitsi_connector.initialize()
        
        assert result is True
        assert jitsi_connector.connected is True
        mock_get.assert_called_once_with(
            f"{jitsi_connector.server_url}/http-pre-bind", 
            timeout=5
        )

def test_initialize_failure(jitsi_connector):
    """Test the initialize method with a failure response."""
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = jitsi_connector.initialize()
        
        assert result is False
        assert jitsi_connector.connected is False
        mock_get.assert_called_once_with(
            f"{jitsi_connector.server_url}/http-pre-bind", 
            timeout=5
        )

def test_create_room(jitsi_connector):
    """Test the create_room method."""
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        room_info = jitsi_connector.create_room()
        
        assert room_info["room_name"] == "test-12345678"
        assert room_info["features"]["video"] is True
        assert room_info["features"]["audio"] is True
        assert room_info["features"]["chat"] is True
        assert len(jitsi_connector.active_rooms) == 1
        assert room_info["room_name"] in jitsi_connector.active_rooms

def test_create_room_with_name(jitsi_connector):
    """Test the create_room method with a specific room name."""
    room_name = "specific-room-name"
    room_info = jitsi_connector.create_room(room_name)
    
    assert room_info["room_name"] == room_name
    assert room_info["features"]["video"] is True
    assert room_info["features"]["audio"] is True
    assert room_info["features"]["chat"] is True
    assert len(jitsi_connector.active_rooms) == 1
    assert room_name in jitsi_connector.active_rooms

def test_join_room(jitsi_connector):
    """Test the join_room method."""
    room_name = "test-room"
    participant_name = "Test User"
    
    # Create a room first
    jitsi_connector.create_room(room_name)
    
    # Join the room
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "98765432-10ab-cdef-ghij-klmnopqrstuv")):
        participant_info = jitsi_connector.join_room(room_name, participant_name)
        
        assert participant_info["id"] == "98765432-10ab-cdef-ghij-klmnopqrstuv"
        assert participant_info["name"] == participant_name
        assert participant_info["features"]["video"] is True
        assert participant_info["features"]["audio"] is True
        assert participant_info["id"] in jitsi_connector.active_rooms[room_name]["participants"]

def test_join_room_auto_create(jitsi_connector):
    """Test that join_room auto-creates a room if it doesn't exist."""
    room_name = "auto-created-room"
    participant_name = "Test User"
    
    # Join a room that doesn't exist yet (should be auto-created)
    participant_info = jitsi_connector.join_room(room_name, participant_name)
    
    assert participant_info["name"] == participant_name
    assert room_name in jitsi_connector.active_rooms
    assert participant_info["id"] in jitsi_connector.active_rooms[room_name]["participants"]

def test_leave_room(jitsi_connector):
    """Test the leave_room method."""
    room_name = "test-room"
    
    # Create a room and add a participant
    jitsi_connector.create_room(room_name)
    participant_info = jitsi_connector.join_room(room_name, "Test User")
    
    # Leave the room
    result = jitsi_connector.leave_room(room_name, participant_info["id"])
    
    assert result is True
    assert participant_info["id"] not in jitsi_connector.active_rooms[room_name]["participants"]

def test_leave_room_last_participant(jitsi_connector):
    """Test that the room is cleaned up when the last participant leaves."""
    room_name = "test-room"
    
    # Create a room and add a participant
    jitsi_connector.create_room(room_name)
    participant_info = jitsi_connector.join_room(room_name, "Test User")
    
    # Leave the room (last participant)
    result = jitsi_connector.leave_room(room_name, participant_info["id"])
    
    assert result is True
    assert room_name not in jitsi_connector.active_rooms  # Room should be cleaned up

def test_leave_nonexistent_room(jitsi_connector):
    """Test leaving a room that doesn't exist."""
    result = jitsi_connector.leave_room("nonexistent-room", "participant-id")
    
    assert result is False

def test_configure_room(jitsi_connector):
    """Test the configure_room method."""
    room_name = "test-room"
    
    # Create a room
    jitsi_connector.create_room(room_name)
    
    # Configure room features
    features = {
        "video": False,
        "chat": False,
        "polls": True
    }
    
    result = jitsi_connector.configure_room(room_name, features)
    
    assert result is True
    assert jitsi_connector.active_rooms[room_name]["features"]["video"] is False
    assert jitsi_connector.active_rooms[room_name]["features"]["chat"] is False
    assert jitsi_connector.active_rooms[room_name]["features"]["polls"] is True
    # Other features should remain unchanged
    assert jitsi_connector.active_rooms[room_name]["features"]["audio"] is True

def test_toggle_participant_feature(jitsi_connector):
    """Test the toggle_participant_feature method."""
    room_name = "test-room"
    
    # Create a room and add a participant
    jitsi_connector.create_room(room_name)
    participant_info = jitsi_connector.join_room(room_name, "Test User")
    
    # Toggle a feature
    result = jitsi_connector.toggle_participant_feature(
        room_name, participant_info["id"], "video", False
    )
    
    assert result is True
    assert jitsi_connector.active_rooms[room_name]["participants"][participant_info["id"]]["features"]["video"] is False
    
    # Video should be disabled but audio should still be enabled
    assert jitsi_connector.active_rooms[room_name]["participants"][participant_info["id"]]["features"]["audio"] is True

def test_get_room_info(jitsi_connector):
    """Test the get_room_info method."""
    room_name = "test-room"
    
    # Create a room
    created_room = jitsi_connector.create_room(room_name)
    
    # Get room info
    room_info = jitsi_connector.get_room_info(room_name)
    
    assert room_info is not None
    assert room_info == created_room
    assert room_info["room_name"] == room_name

def test_get_participant_info(jitsi_connector):
    """Test the get_participant_info method."""
    room_name = "test-room"
    
    # Create a room and add a participant
    jitsi_connector.create_room(room_name)
    participant_info = jitsi_connector.join_room(room_name, "Test User")
    
    # Get participant info
    retrieved_info = jitsi_connector.get_participant_info(room_name, participant_info["id"])
    
    assert retrieved_info is not None
    assert retrieved_info == participant_info
    assert retrieved_info["name"] == "Test User"

def test_get_jitsi_url(jitsi_connector):
    """Test the get_jitsi_url method."""
    room_name = "test-room"
    url = jitsi_connector.get_jitsi_url(room_name)
    
    assert url == f"{jitsi_connector.server_url}/{room_name}"

@pytest.mark.asyncio
async def test_connect_websocket(jitsi_connector):
    """Test the connect_websocket method."""
    room_name = "test-room"
    
    # Mock websocket
    mock_websocket = AsyncMock()
    
    with patch('websockets.connect', return_value=mock_websocket) as mock_connect:
        result = await jitsi_connector.connect_websocket(room_name)
        
        assert result is True
        assert jitsi_connector.websocket == mock_websocket
        mock_connect.assert_called_once_with(
            "wss://test.jitsi.meet/xmpp-websocket"
        )
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["action"] == "join"
        assert sent_data["room"] == room_name

def test_disconnect(jitsi_connector):
    """Test the disconnect method."""
    # Connect and then disconnect
    with patch.object(jitsi_connector, 'websocket', new=AsyncMock()) as mock_websocket:
        jitsi_connector.connected = True
        jitsi_connector.disconnect()
        
        assert jitsi_connector.connected is False
        # verify that a close task was created for the websocket
        import asyncio
        assert isinstance(asyncio.create_task.call_args[0][0], type(mock_websocket.close()))