# tests/test_jitsi_connector_complete.py (continued)
import pytest
import uuid
import json
import asyncio
import websockets
from unittest.mock import Mock, patch, AsyncMock, MagicMock

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

def test_get_room_info_nonexistent(jitsi_connector):
    """Test getting info for a nonexistent room."""
    room_info = jitsi_connector.get_room_info("nonexistent-room")
    
    assert room_info is None

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

def test_get_participant_info_nonexistent_room(jitsi_connector):
    """Test getting participant info from a nonexistent room."""
    participant_info = jitsi_connector.get_participant_info("nonexistent-room", "participant-id")
    
    assert participant_info is None

def test_get_participant_info_nonexistent_participant(jitsi_connector):
    """Test getting info for a nonexistent participant."""
    room_name = "test-room"
    
    # Create a room
    jitsi_connector.create_room(room_name)
    
    # Get info for a nonexistent participant
    participant_info = jitsi_connector.get_participant_info(room_name, "nonexistent-participant")
    
    assert participant_info is None

def test_get_jitsi_url(jitsi_connector):
    """Test the get_jitsi_url method."""
    room_name = "test-room"
    url = jitsi_connector.get_jitsi_url(room_name)
    
    assert url == f"{jitsi_connector.server_url}/{room_name}"

@pytest.mark.asyncio
async def test_connect_websocket(jitsi_connector):
    """Test the connect_websocket method."""
    room_name = "test-room"
    
    # Create a real-like mock that doesn't cause awaiting issues
    class MockWebsocket:
        async def send(self, data):
            return None
        
    mock_websocket = MockWebsocket()
    
    # Use your custom mock instead of AsyncMock which causes issues
    with patch('websockets.connect', return_value=mock_websocket), \
         patch('asyncio.ensure_future'):
        
        # Call the method
        result = await jitsi_connector.connect_websocket(room_name)
        
        # Verify success
        assert result is True

@pytest.mark.asyncio
async def test_connect_websocket_exception(jitsi_connector):
    """Test the connect_websocket method with an exception."""
    room_name = "test-room"
    
    # Mock websocket.connect to raise an exception
    with patch('websockets.connect', side_effect=Exception("Test error")):
        result = await jitsi_connector.connect_websocket(room_name)
        
        assert result is False
        assert jitsi_connector.websocket is None

@pytest.mark.asyncio
async def test_websocket_listener(jitsi_connector):
    """Test the _websocket_listener method."""
    # Set up mock callbacks
    jitsi_connector.on_participant_joined = Mock()
    jitsi_connector.on_participant_left = Mock()
    jitsi_connector.on_message_received = Mock()
    
    # Mock websocket
    mock_websocket = AsyncMock()
    jitsi_connector.websocket = mock_websocket
    
    # Mock messages
    messages = [
        json.dumps({
            "type": "participant_joined",
            "room": "test-room",
            "participant": {"id": "participant-id", "name": "Test User"}
        }),
        json.dumps({
            "type": "participant_left",
            "room": "test-room",
            "participant": {"id": "participant-id", "name": "Test User"}
        }),
        json.dumps({
            "type": "message",
            "room": "test-room",
            "from": "participant-id",
            "message": "Hello, world!"
        }),
        websockets.exceptions.ConnectionClosed(None, None)  # To exit the loop
    ]
    
    # Mock receive method to return the messages
    mock_websocket.recv.side_effect = messages
    
    # Run the listener
    await jitsi_connector._websocket_listener()
    
    # Check that callbacks were called
    jitsi_connector.on_participant_joined.assert_called_once_with(
        "test-room", {"id": "participant-id", "name": "Test User"}
    )
    jitsi_connector.on_participant_left.assert_called_once_with(
        "test-room", {"id": "participant-id", "name": "Test User"}
    )
    jitsi_connector.on_message_received.assert_called_once_with(
        "test-room", "participant-id", "Hello, world!"
    )

@pytest.mark.asyncio
async def test_websocket_listener_exception(jitsi_connector):
    """Test the _websocket_listener method with an exception."""
    # Mock websocket
    mock_websocket = AsyncMock()
    jitsi_connector.websocket = mock_websocket
    
    # Mock receive method to raise an exception
    mock_websocket.recv.side_effect = Exception("Test error")
    
    # Run the listener
    await jitsi_connector._websocket_listener()
    
    # Just checking that the function handles the exception without crashing

def test_disconnect(jitsi_connector):
    """Test the disconnect method."""
    # Connect and then disconnect
    with patch.object(jitsi_connector, 'websocket', new=AsyncMock()) as mock_websocket, \
         patch('asyncio.create_task') as mock_create_task:
        
        jitsi_connector.connected = True
        jitsi_connector.disconnect()
        
        assert jitsi_connector.connected is False
        mock_create_task.assert_called_once()
        # Ensure a close task was created for the websocket
        assert isinstance(mock_create_task.call_args[0][0], type(mock_websocket.close()))

def test_disconnect_without_websocket(jitsi_connector):
    """Test disconnecting when there is no websocket."""
    jitsi_connector.connected = True
    jitsi_connector.websocket = None
    
    # Should not raise any exception
    jitsi_connector.disconnect()
    
    assert jitsi_connector.connected is False