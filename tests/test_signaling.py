# tests/test_signaling.py
import pytest
import json
import asyncio
import websockets
from unittest.mock import Mock, patch, AsyncMock

from jitsi_plus_plugin.core.signaling import SignalingServer

@pytest.fixture
def signaling_server():
    """Create a SignalingServer instance with test configuration."""
    config = {
        "host": "127.0.0.1",
        "port": 8080,
        "use_ssl": False
    }
    return SignalingServer(config)

@pytest.mark.asyncio
async def test_handle_connection(signaling_server):
    """Test the _handle_connection method."""
    # Mock websocket
    mock_websocket = AsyncMock()
    mock_websocket.__aiter__.return_value = [
        json.dumps({"type": "join", "roomId": "test-room", "userInfo": {"name": "Test User"}}),
        json.dumps({"type": "feature", "roomId": "test-room", "feature": "video", "enabled": False}),
        json.dumps({"type": "leave", "roomId": "test-room"})
    ]
    
    # Mock path
    mock_path = "/ws"
    
    # Patch handle_message
    with patch.object(signaling_server, '_handle_message', AsyncMock()) as mock_handle_message:
        with patch.object(signaling_server, '_handle_disconnect', AsyncMock()) as mock_handle_disconnect:
            # Call handle_connection
            await signaling_server._handle_connection(mock_websocket, mock_path)
            
            # Check if welcome message was sent
            mock_websocket.send.assert_called()
            welcome_msg = json.loads(mock_websocket.send.call_args_list[0][0][0])
            assert welcome_msg["type"] == "welcome"
            assert "connectionId" in welcome_msg
            
            # Check if messages were handled
            assert mock_handle_message.call_count == 3
            
            # Check if disconnect was handled
            mock_handle_disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_handle_join(signaling_server):
    """Test the _handle_join method."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    user_info = {"name": "Test User"}
    
    # Mock websocket
    mock_websocket = AsyncMock()
    signaling_server.active_connections[connection_id] = mock_websocket
    
    # Call handle_join
    await signaling_server._handle_join(connection_id, room_id, user_info)
    
    # Check if connection was added to room
    assert connection_id in signaling_server.room_connections[room_id]
    assert room_id in signaling_server.connection_rooms[connection_id]
    
    # Check if user info was stored
    assert signaling_server.features_states[connection_id]["user_info"] == user_info
    
    # Check if room state was sent to the client
    mock_websocket.send.assert_called_once()
    room_state_msg = json.loads(mock_websocket.send.call_args[0][0])
    assert room_state_msg["type"] == "room_state"
    assert room_state_msg["roomId"] == room_id

@pytest.mark.asyncio
async def test_handle_leave(signaling_server):
    """Test the _handle_leave method."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    
    # Create room and add connection
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.connection_rooms[connection_id] = {room_id}
    
    # Call handle_leave
    await signaling_server._handle_leave(connection_id, room_id)
    
    # Check if connection was removed from room
    assert connection_id not in signaling_server.room_connections[room_id]
    assert room_id not in signaling_server.connection_rooms[connection_id]

@pytest.mark.asyncio
async def test_handle_leave_last_user(signaling_server):
    """Test the _handle_leave method when the last user leaves."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    
    # Create room and add connection
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.connection_rooms[connection_id] = {room_id}
    signaling_server.room_states[room_id] = {"features": {}}
    
    # Call handle_leave
    await signaling_server._handle_leave(connection_id, room_id)
    
    # Check if room was cleaned up
    assert room_id not in signaling_server.room_connections
    assert room_id not in signaling_server.room_states

@pytest.mark.asyncio
async def test_handle_disconnect(signaling_server):
    """Test the _handle_disconnect method."""
    # Setup connection and multiple rooms
    connection_id = "test-connection"
    room1_id = "test-room-1"
    room2_id = "test-room-2"
    
    # Create rooms and add connection
    signaling_server.room_connections[room1_id] = {connection_id}
    signaling_server.room_connections[room2_id] = {connection_id}
    signaling_server.connection_rooms[connection_id] = {room1_id, room2_id}
    signaling_server.active_connections[connection_id] = AsyncMock()
    signaling_server.features_states[connection_id] = {"user_info": {}}
    
    # Patch handle_leave
    with patch.object(signaling_server, '_handle_leave', AsyncMock()) as mock_handle_leave:
        # Call handle_disconnect
        await signaling_server._handle_disconnect(connection_id)
        
        # Check if handle_leave was called for each room
        assert mock_handle_leave.call_count == 2
        mock_handle_leave.assert_any_call(connection_id, room1_id)
        mock_handle_leave.assert_any_call(connection_id, room2_id)
        
        # Check if connection resources were cleaned up
        assert connection_id not in signaling_server.connection_rooms
        assert connection_id not in signaling_server.active_connections
        assert connection_id not in signaling_server.features_states

@pytest.mark.asyncio
async def test_handle_feature_toggle_room(signaling_server):
    """Test the _handle_feature_toggle method for room features."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    feature = "video"
    enabled = False
    target = "room"
    
    # Create room and add connection
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "features": {
            "video": True,
            "audio": True
        }
    }
    
    # Call handle_feature_toggle
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_feature_toggle(connection_id, room_id, feature, enabled, target)
        
        # Check if feature was toggled
        assert signaling_server.room_states[room_id]["features"][feature] == enabled
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once_with(
            room_id,
            {
                "type": "feature_toggle",
                "roomId": room_id,
                "feature": feature,
                "enabled": enabled,
                "target": "room",
                "userId": connection_id
            }
        )

@pytest.mark.asyncio
async def test_handle_feature_toggle_user(signaling_server):
    """Test the _handle_feature_toggle method for user features."""
    # Setup connections and room
    connection_id = "test-connection"
    target_connection_id = "target-connection"
    room_id = "test-room"
    feature = "audio"
    enabled = False
    
    # Create room and add connections
    signaling_server.room_connections[room_id] = {connection_id, target_connection_id}
    signaling_server.features_states[target_connection_id] = {
        "user_info": {"name": "Target User"},
        "features": {
            "video": True,
            "audio": True
        }
    }
    
    # Call handle_feature_toggle
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_feature_toggle(
            connection_id, room_id, feature, enabled, target_connection_id
        )
        
        # Check if feature was toggled
        assert signaling_server.features_states[target_connection_id]["features"][feature] == enabled
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once_with(
            room_id,
            {
                "type": "feature_toggle",
                "roomId": room_id,
                "feature": feature,
                "enabled": enabled,
                "target": target_connection_id,
                "userId": connection_id
            }
        )

@pytest.mark.asyncio
async def test_handle_whiteboard_event(signaling_server):
    """Test the _handle_whiteboard_event method."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    
    # Create room and state
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "whiteboard": {
            "elements": []
        }
    }
    
    # Test adding an element
    event = {
        "type": "add",
        "element": {
            "id": "test-element",
            "type": "path",
            "data": {"points": [[0, 0], [10, 10]]}
        }
    }
    
    # Call handle_whiteboard_event
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_whiteboard_event(connection_id, room_id, event)
        
        # Check if element was added
        assert len(signaling_server.room_states[room_id]["whiteboard"]["elements"]) == 1
        assert signaling_server.room_states[room_id]["whiteboard"]["elements"][0]["id"] == "test-element"
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once_with(
            room_id,
            {
                "type": "whiteboard_event",
                "roomId": room_id,
                "userId": connection_id,
                "event": event
            }
        )
    
    # Test updating an element
    element_id = "test-element"
    update_event = {
        "type": "update",
        "elementId": element_id,
        "updates": {
            "data": {"points": [[0, 0], [10, 10], [20, 20]]}
        }
    }
    
    # Call handle_whiteboard_event again
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_whiteboard_event(connection_id, room_id, update_event)
        
        # Check if element was updated
        element = signaling_server.room_states[room_id]["whiteboard"]["elements"][0]
        assert len(element["data"]["points"]) == 3
        assert element["data"]["points"][2] == [20, 20]
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()
    
    # Test clearing the whiteboard
    clear_event = {
        "type": "clear"
    }
    
    # Call handle_whiteboard_event again
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_whiteboard_event(connection_id, room_id, clear_event)
        
        # Check if whiteboard was cleared
        assert len(signaling_server.room_states[room_id]["whiteboard"]["elements"]) == 0
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()

@pytest.mark.asyncio
async def test_handle_poll_event_create(signaling_server):
    """Test the _handle_poll_event method for creating a poll."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    
    # Create room and state
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "polls": []
    }
    
    # Test creating a poll
    poll_action = "create"
    poll_data = {
        "question": "Test question?",
        "options": ["Option 1", "Option 2", "Option 3"]
    }
    
    # Call handle_poll_event
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_poll_event(connection_id, room_id, poll_action, poll_data)
        
        # Check if poll was created
        assert len(signaling_server.room_states[room_id]["polls"]) == 1
        poll = signaling_server.room_states[room_id]["polls"][0]
        assert poll["question"] == "Test question?"
        assert len(poll["options"]) == 3
        assert poll["creator"] == connection_id
        assert poll["active"] is True
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][1]
        assert broadcast_data["type"] == "poll_created"
        assert broadcast_data["poll"]["question"] == "Test question?"

@pytest.mark.asyncio
async def test_handle_poll_event_vote(signaling_server):
    """Test the _handle_poll_event method for voting in a poll."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    poll_id = "test-poll"
    
    # Create room and poll
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "polls": [
            {
                "id": poll_id,
                "question": "Test question?",
                "options": ["Option 1", "Option 2", "Option 3"],
                "creator": connection_id,
                "active": True,
                "votes": {}
            }
        ]
    }
    
    # Test voting in a poll
    poll_action = "vote"
    poll_data = {
        "pollId": poll_id,
        "optionIndex": 1  # Vote for Option 2
    }
    
    # Call handle_poll_event
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_poll_event(connection_id, room_id, poll_action, poll_data)
        
        # Check if vote was recorded
        poll = signaling_server.room_states[room_id]["polls"][0]
        assert connection_id in poll["votes"]
        assert poll["votes"][connection_id] == 1
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][1]
        assert broadcast_data["type"] == "poll_vote"
        assert broadcast_data["pollId"] == poll_id
        assert broadcast_data["optionIndex"] == 1

@pytest.mark.asyncio
async def test_handle_poll_event_end(signaling_server):
    """Test the _handle_poll_event method for ending a poll."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    poll_id = "test-poll"
    
    # Create room and poll with some votes
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "polls": [
            {
                "id": poll_id,
                "question": "Test question?",
                "options": ["Option 1", "Option 2", "Option 3"],
                "creator": connection_id,
                "active": True,
                "votes": {
                    "user1": 0,
                    "user2": 1,
                    "user3": 1,
                    "user4": 2
                }
            }
        ]
    }
    
    # Test ending a poll
    poll_action = "end"
    poll_data = {
        "pollId": poll_id
    }
    
    # Call handle_poll_event
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_poll_event(connection_id, room_id, poll_action, poll_data)
        
        # Check if poll was ended
        poll = signaling_server.room_states[room_id]["polls"][0]
        assert poll["active"] is False
        assert "ended_at" in poll
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][1]
        assert broadcast_data["type"] == "poll_ended"
        assert broadcast_data["pollId"] == poll_id
        
        # Check results
        assert broadcast_data["results"] == [1, 2, 1]  # Counts for each option

@pytest.mark.asyncio
async def test_handle_chat_message(signaling_server):
    """Test the _handle_chat_message method."""
    # Setup connection and room
    connection_id = "test-connection"
    room_id = "test-room"
    message_content = "Hello, world!"
    
    # Create room and state
    signaling_server.room_connections[room_id] = {connection_id}
    signaling_server.room_states[room_id] = {
        "messages": []
    }
    
    # Call handle_chat_message
    with patch.object(signaling_server, '_broadcast_to_room', AsyncMock()) as mock_broadcast:
        await signaling_server._handle_chat_message(connection_id, room_id, message_content)
        
        # Check if message was stored
        assert len(signaling_server.room_states[room_id]["messages"]) == 1
        message = signaling_server.room_states[room_id]["messages"][0]
        assert message["sender"] == connection_id
        assert message["content"] == message_content
        
        # Check if broadcast was called
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][1]
        assert broadcast_data["type"] == "chat_message"
        assert broadcast_data["message"]["content"] == message_content

@pytest.mark.asyncio
async def test_handle_custom_event(signaling_server):
    """Test the _handle_custom_event method."""
    # Setup connection
    connection_id = "test-connection"
    event_name = "custom_event"
    event_data = {"key": "value"}
    
    # Setup event handler
    mock_handler = Mock(return_value={"result": "success"})
    signaling_server.event_handlers[event_name] = mock_handler
    
    # Setup websocket
    mock_websocket = AsyncMock()
    signaling_server.active_connections[connection_id] = mock_websocket
    
    # Call handle_custom_event
    await signaling_server._handle_custom_event(connection_id, event_name, event_data)
    
    # Check if handler was called
    mock_handler.assert_called_once_with(connection_id, event_data)
    
    # Check if response was sent
    mock_websocket.send.assert_called_once()
    response_data = json.loads(mock_websocket.send.call_args[0][0])
    assert response_data["type"] == "custom_event_response"
    assert response_data["event"] == event_name
    assert response_data["data"] == {"result": "success"}

@pytest.mark.asyncio
async def test_broadcast_to_room(signaling_server):
    """Test the _broadcast_to_room method."""
    # Setup room with multiple connections
    room_id = "test-room"
    connection1 = "connection1"
    connection2 = "connection2"
    connection3 = "connection3"
    
    # Create websockets
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()
    mock_websocket3 = AsyncMock()
    
    # Setup connections
    signaling_server.room_connections[room_id] = {connection1, connection2, connection3}
    signaling_server.active_connections[connection1] = mock_websocket1
    signaling_server.active_connections[connection2] = mock_websocket2
    signaling_server.active_connections[connection3] = mock_websocket3
    
    # Message to broadcast
    message = {
        "type": "test_message",
        "data": "test_data"
    }
    
    # Call broadcast_to_room
    await signaling_server._broadcast_to_room(room_id, message)
    
    # Check if all websockets received the message
    message_json = json.dumps(message)
    mock_websocket1.send.assert_called_once_with(message_json)
    mock_websocket2.send.assert_called_once_with(message_json)
    mock_websocket3.send.assert_called_once_with(message_json)

@pytest.mark.asyncio
async def test_broadcast_to_room_with_exclude(signaling_server):
    """Test the _broadcast_to_room method with exclusions."""
    # Setup room with multiple connections
    room_id = "test-room"
    connection1 = "connection1"
    connection2 = "connection2"
    connection3 = "connection3"
    
    # Create websockets
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()
    mock_websocket3 = AsyncMock()
    
    # Setup connections
    signaling_server.room_connections[room_id] = {connection1, connection2, connection3}
    signaling_server.active_connections[connection1] = mock_websocket1
    signaling_server.active_connections[connection2] = mock_websocket2
    signaling_server.active_connections[connection3] = mock_websocket3
    
    # Message to broadcast
    message = {
        "type": "test_message",
        "data": "test_data"
    }
    
    # Call broadcast_to_room with exclusion
    await signaling_server._broadcast_to_room(room_id, message, exclude=[connection2])
    
    # Check if websockets 1 and 3 received the message, but not 2
    message_json = json.dumps(message)
    mock_websocket1.send.assert_called_once_with(message_json)
    mock_websocket2.send.assert_not_called()
    mock_websocket3.send.assert_called_once_with(message_json)

def test_register_event_handler(signaling_server):
    """Test the register_event_handler method."""
    event_name = "custom_event"
    mock_handler = Mock()
    
    # Register handler
    signaling_server.register_event_handler(event_name, mock_handler)
    
    # Check if handler was registered
    assert event_name in signaling_server.event_handlers
    assert signaling_server.event_handlers[event_name] == mock_handler

def test_unregister_event_handler(signaling_server):
    """Test the unregister_event_handler method."""
    event_name = "custom_event"
    mock_handler = Mock()
    
    # Register and then unregister handler
    signaling_server.register_event_handler(event_name, mock_handler)
    signaling_server.unregister_event_handler(event_name)
    
    # Check if handler was unregistered
    assert event_name not in signaling_server.event_handlers

def test_start_stop_server(signaling_server):
    """Test starting and stopping the server."""
    # Mock for threading and asyncio
    with patch('threading.Thread') as mock_thread:
        # Start server
        result = signaling_server.start()
        
        assert result is True
        assert signaling_server.is_running is True
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        
        # Start server again (should warn and return)
        signaling_server.start()
        
        # Should still be called only once
        assert mock_thread.call_count == 1
        
        # Stop server
        with patch.object(signaling_server, '_stop_server', AsyncMock()) as mock_stop:
            signaling_server.server = Mock()
            result = signaling_server.stop()
            
            assert result is True
            assert signaling_server.is_running is False
            mock_stop.assert_called_once()