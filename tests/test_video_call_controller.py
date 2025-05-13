# tests/test_whiteboard_controller_fixed.py
import pytest
import uuid
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from jitsi_plus_plugin.features.whiteboard import WhiteboardController

@pytest.fixture
def mock_signaling_server():
    """Create a mock SignalingServer."""
    mock = Mock()
    
    # Mock room_states
    mock.room_states = {
        "test-room": {
            "created_at": 1234567890
        }
    }
    
    # Mock _handle_whiteboard_event method
    mock._handle_whiteboard_event = AsyncMock()
    
    return mock

@pytest.fixture
def whiteboard_controller(mock_signaling_server):
    """Create a WhiteboardController with a mocked SignalingServer."""
    return WhiteboardController(mock_signaling_server)

def test_create_whiteboard(whiteboard_controller, mock_signaling_server):
    """Test creating a whiteboard."""
    room_id = "test-room"
    
    whiteboard_info = whiteboard_controller.create_whiteboard(room_id)
    
    # Check whiteboard info
    assert whiteboard_info["id"] == f"wb-{room_id}"
    assert whiteboard_info["room_id"] == room_id
    assert whiteboard_info["created_at"] == 1234567890
    assert whiteboard_info["elements"] == []
    assert whiteboard_info["active_users"] == set()
    
    # Check that whiteboard was stored
    assert f"wb-{room_id}" in whiteboard_controller.active_whiteboards
    assert whiteboard_controller.active_whiteboards[f"wb-{room_id}"] == whiteboard_info

def test_create_whiteboard_nonexistent_room(whiteboard_controller, mock_signaling_server):
    """Test creating a whiteboard for a room that doesn't exist in the signaling server."""
    room_id = "nonexistent-room"
    
    # Room doesn't exist in signaling_server.room_states
    whiteboard_info = whiteboard_controller.create_whiteboard(room_id)
    
    # Should still create the whiteboard
    assert whiteboard_info["id"] == f"wb-{room_id}"
    assert whiteboard_info["room_id"] == room_id
    assert whiteboard_info["created_at"] == 0  # Default value
    assert whiteboard_info["elements"] == []
    assert whiteboard_info["active_users"] == set()

def test_get_whiteboard(whiteboard_controller):
    """Test getting a whiteboard."""
    room_id = "test-room"
    
    # Create a whiteboard first
    created_info = whiteboard_controller.create_whiteboard(room_id)
    
    # Get the whiteboard
    whiteboard_info = whiteboard_controller.get_whiteboard(room_id)
    
    # Check that we got the same info back
    assert whiteboard_info is created_info
    assert whiteboard_info["id"] == f"wb-{room_id}"
    assert whiteboard_info["room_id"] == room_id

def test_get_whiteboard_nonexistent(whiteboard_controller):
    """Test getting a whiteboard that doesn't exist."""
    room_id = "nonexistent-room"
    
    whiteboard_info = whiteboard_controller.get_whiteboard(room_id)
    
    assert whiteboard_info is None

def test_join_whiteboard(whiteboard_controller):
    """Test joining a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Join the whiteboard
    result = whiteboard_controller.join_whiteboard(room_id, user_id)
    
    # Check result
    assert result is True
    
    # Check that user was added to the whiteboard's active users
    whiteboard_id = f"wb-{room_id}"
    assert whiteboard_id in whiteboard_controller.active_whiteboards
    assert user_id in whiteboard_controller.active_whiteboards[whiteboard_id]["active_users"]

def test_join_whiteboard_auto_create(whiteboard_controller):
    """Test that join_whiteboard auto-creates a whiteboard if it doesn't exist."""
    room_id = "auto-create-room"
    user_id = "test-user"
    
    # Join a whiteboard that doesn't exist yet
    result = whiteboard_controller.join_whiteboard(room_id, user_id)
    
    # Check result
    assert result is True
    
    # Check that whiteboard was created and user was added
    whiteboard_id = f"wb-{room_id}"
    assert whiteboard_id in whiteboard_controller.active_whiteboards
    assert user_id in whiteboard_controller.active_whiteboards[whiteboard_id]["active_users"]

def test_leave_whiteboard(whiteboard_controller):
    """Test leaving a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create whiteboard and add user
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    whiteboard_controller.active_whiteboards[whiteboard_id]["active_users"].add(user_id)
    
    # Leave the whiteboard
    result = whiteboard_controller.leave_whiteboard(room_id, user_id)
    
    # Check result
    assert result is True
    
    # Check that user was removed from the whiteboard's active users
    assert whiteboard_id in whiteboard_controller.active_whiteboards
    assert user_id not in whiteboard_controller.active_whiteboards[whiteboard_id]["active_users"]

def test_leave_whiteboard_last_user(whiteboard_controller):
    """Test that the whiteboard is cleaned up when the last user leaves."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create whiteboard and add user
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    whiteboard_controller.active_whiteboards[whiteboard_id]["active_users"].add(user_id)
    
    # Leave the whiteboard
    result = whiteboard_controller.leave_whiteboard(room_id, user_id)
    
    # Check result
    assert result is True
    
    # Check that whiteboard was removed from active_whiteboards
    assert whiteboard_id not in whiteboard_controller.active_whiteboards

def test_leave_nonexistent_whiteboard(whiteboard_controller):
    """Test leaving a whiteboard that doesn't exist."""
    room_id = "nonexistent-room"
    user_id = "test-user"
    
    result = whiteboard_controller.leave_whiteboard(room_id, user_id)
    
    assert result is False

def test_add_element(whiteboard_controller, mock_signaling_server):
    """Test adding an element to a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    element_data = {
        "type": "path",
        "data": {"points": [[10, 10], [20, 20], [30, 30]]},
        "style": {"stroke": "black", "strokeWidth": 2}
    }
    
    # Create a whiteboard first
    whiteboard_controller.create_whiteboard(room_id)
    
    # Patch asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task, \
         patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        # Add an element
        element = whiteboard_controller.add_element(room_id, element_data, user_id)
        
        # Check element info
        assert element["id"] == "12345678-90ab-cdef-ghij-klmnopqrstuv"
        assert element["type"] == "path"
        assert element["data"] == {"points": [[10, 10], [20, 20], [30, 30]]}
        assert element["style"] == {"stroke": "black", "strokeWidth": 2}
        assert element["creator"] == user_id
        assert element["created_at"] == 1234567890
        
        # Check that element was added to the whiteboard
        whiteboard_id = f"wb-{room_id}"
        assert whiteboard_controller.active_whiteboards[whiteboard_id]["elements"] == [element]
        
        # Check that signaling server was notified via create_task
        mock_create_task.assert_called_once()

def test_add_element_auto_create(whiteboard_controller, mock_signaling_server):
    """Test that add_element auto-creates a whiteboard if it doesn't exist."""
    room_id = "auto-create-room"
    user_id = "test-user"
    element_data = {
        "type": "path",
        "data": {"points": [[10, 10], [20, 20], [30, 30]]},
        "style": {"stroke": "black", "strokeWidth": 2}
    }
    
    # Patch asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task, \
         patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")):
        # Add an element (no whiteboard exists yet)
        element = whiteboard_controller.add_element(room_id, element_data, user_id)
        
        # Check that whiteboard was created
        whiteboard_id = f"wb-{room_id}"
        assert whiteboard_id in whiteboard_controller.active_whiteboards
        
        # Check that element was added
        assert len(whiteboard_controller.active_whiteboards[whiteboard_id]["elements"]) == 1
        assert whiteboard_controller.active_whiteboards[whiteboard_id]["elements"][0] == element

def test_update_element(whiteboard_controller, mock_signaling_server):
    """Test updating an element on a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard and add an element
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    
    element = {
        "id": "element-123",
        "type": "path",
        "data": {"points": [[10, 10], [20, 20]]},
        "style": {"stroke": "black", "strokeWidth": 2},
        "creator": user_id,
        "created_at": 1234567890
    }
    
    # Add the element directly to avoid asyncio.create_task issues
    whiteboard_controller.active_whiteboards[whiteboard_id]["elements"].append(element)
    
    # Update the element
    updates = {
        "data": {"points": [[10, 10], [20, 20], [30, 30]]},
        "style": {"stroke": "red"}
    }
    
    # Patch asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task:
        result = whiteboard_controller.update_element(room_id, element["id"], updates, user_id)
        
        # Check result
        assert result is True
        
        # Check that element was updated
        updated_element = whiteboard_controller.active_whiteboards[whiteboard_id]["elements"][0]
        assert updated_element["data"]["points"] == [[10, 10], [20, 20], [30, 30]]
        assert updated_element["style"]["stroke"] == "red"
        assert updated_element["style"]["strokeWidth"] == 2  # Unchanged
        
        # Check that signaling server was notified
        mock_create_task.assert_called_once()

def test_update_nonexistent_element(whiteboard_controller, mock_signaling_server):
    """Test updating an element that doesn't exist."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard
    whiteboard_controller.create_whiteboard(room_id)
    
    # Update a nonexistent element
    result = whiteboard_controller.update_element(room_id, "nonexistent-element", {}, user_id)
    
    # Check result
    assert result is False

def test_delete_element(whiteboard_controller, mock_signaling_server):
    """Test deleting an element from a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard and add an element
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    
    element = {
        "id": "element-123",
        "type": "path",
        "creator": user_id,
        "created_at": 1234567890
    }
    
    # Add the element directly
    whiteboard_controller.active_whiteboards[whiteboard_id]["elements"].append(element)
    
    # Patch asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task:
        # Delete the element
        result = whiteboard_controller.delete_element(room_id, element["id"], user_id)
        
        # Check result
        assert result is True
        
        # Check that element was removed
        assert whiteboard_controller.active_whiteboards[whiteboard_id]["elements"] == []
        
        # Check that signaling server was notified
        mock_create_task.assert_called_once()

def test_delete_nonexistent_element(whiteboard_controller, mock_signaling_server):
    """Test deleting an element that doesn't exist."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard
    whiteboard_controller.create_whiteboard(room_id)
    
    # Delete a nonexistent element
    result = whiteboard_controller.delete_element(room_id, "nonexistent-element", user_id)
    
    # Check result
    assert result is False

def test_clear_whiteboard(whiteboard_controller, mock_signaling_server):
    """Test clearing all elements from a whiteboard."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard and add some elements
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    
    # Add elements directly
    whiteboard_controller.active_whiteboards[whiteboard_id]["elements"] = [
        {"id": "element-1", "type": "path"},
        {"id": "element-2", "type": "rect"}
    ]
    
    # Patch asyncio.create_task
    with patch('asyncio.create_task') as mock_create_task:
        # Clear the whiteboard
        result = whiteboard_controller.clear_whiteboard(room_id, user_id)
        
        # Check result
        assert result is True
        
        # Check that all elements were removed
        assert whiteboard_controller.active_whiteboards[whiteboard_id]["elements"] == []
        
        # Check that signaling server was notified
        mock_create_task.assert_called_once()

def test_clear_nonexistent_whiteboard(whiteboard_controller, mock_signaling_server):
    """Test clearing a whiteboard that doesn't exist."""
    room_id = "nonexistent-room"
    user_id = "test-user"
    
    result = whiteboard_controller.clear_whiteboard(room_id, user_id)
    
    # Check result
    assert result is False

def test_export_whiteboard_json(whiteboard_controller):
    """Test exporting a whiteboard as JSON."""
    room_id = "test-room"
    user_id = "test-user"
    
    # Create a whiteboard and add an element
    whiteboard_controller.create_whiteboard(room_id)
    whiteboard_id = f"wb-{room_id}"
    
    element = {
        "id": "element-123",
        "type": "path",
        "creator": user_id,
        "created_at": 1234567890
    }
    
    # Add the element directly
    whiteboard_controller.active_whiteboards[whiteboard_id]["elements"].append(element)
    
    # Export the whiteboard as JSON
    export_data = whiteboard_controller.export_whiteboard(room_id, "json")
    
    # Check export data
    assert export_data["id"] == whiteboard_id
    assert export_data["elements"] == [element]

def test_export_whiteboard_unsupported_format(whiteboard_controller):
    """Test exporting a whiteboard in an unsupported format."""
    room_id = "test-room"
    
    # Create a whiteboard
    whiteboard_controller.create_whiteboard(room_id)
    
    # Try to export in an unsupported format
    with pytest.raises(ValueError, match="Unsupported export format: invalid"):
        whiteboard_controller.export_whiteboard(room_id, "invalid")

def test_export_nonexistent_whiteboard(whiteboard_controller):
    """Test exporting a whiteboard that doesn't exist."""
    room_id = "nonexistent-room"
    
    export_data = whiteboard_controller.export_whiteboard(room_id, "json")
    
    assert export_data is None