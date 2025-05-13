# tests/test_poll_controller.py
import pytest
import uuid
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from jitsi_plus_plugin.features.polls import PollController

@pytest.fixture
def mock_signaling_server():
    """Create a mock SignalingServer."""
    mock = Mock()
    
    # Mock _handle_poll_event method
    mock._handle_poll_event = AsyncMock()
    
    return mock

@pytest.fixture
def poll_controller(mock_signaling_server):
    """Create a PollController with a mocked SignalingServer."""
    return PollController(mock_signaling_server)

def test_create_poll(poll_controller, mock_signaling_server):
    """Test creating a poll."""
    room_id = "test-room"
    creator_id = "test-creator"
    question = "What is your favorite color?"
    options = ["Red", "Green", "Blue"]
    
    # Mock uuid.uuid4 and time.time
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task') as mock_create_task:
        
        poll_info = poll_controller.create_poll(room_id, question, options, creator_id)
        
        # Check poll info
        assert poll_info["id"] == "12345678-90ab-cdef-ghij-klmnopqrstuv"
        assert poll_info["room_id"] == room_id
        assert poll_info["question"] == question
        assert poll_info["options"] == options
        assert poll_info["creator_id"] == creator_id
        assert poll_info["created_at"] == 1234567890
        assert poll_info["active"] is True
        assert poll_info["anonymous"] is False
        assert poll_info["votes"] == {}
        assert poll_info["results"] is None
        
        # Check that poll was stored
        assert poll_info["id"] in poll_controller.active_polls
        assert poll_controller.active_polls[poll_info["id"]] == poll_info
        
        # Check that signaling server was notified
        mock_create_task.assert_called_once()
        call_args = mock_create_task.call_args[0][0]
        assert isinstance(call_args, type(mock_signaling_server._handle_poll_event()))
        # Can't directly check the args to _handle_poll_event since it's wrapped in a coroutine

def test_create_anonymous_poll(poll_controller):
    """Test creating an anonymous poll."""
    room_id = "test-room"
    creator_id = "test-creator"
    question = "What is your favorite color?"
    options = ["Red", "Green", "Blue"]
    anonymous = True
    
    # Mock uuid.uuid4 and time.time
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "12345678-90ab-cdef-ghij-klmnopqrstuv")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(room_id, question, options, creator_id, anonymous)
        
        # Check that the poll is anonymous
        assert poll_info["anonymous"] is True

def test_vote(poll_controller, mock_signaling_server):
    """Test voting in a poll."""
    room_id = "test-room"
    user_id = "test-user"
    option_index = 1  # "Green"
    
    # Create a poll first
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], "test-creator"
        )
        
        # Reset the mocks
        mock_signaling_server._handle_poll_event.reset_mock()
        
        # Vote in the poll
        with patch('asyncio.create_task') as mock_create_task:
            result = poll_controller.vote(poll_info["id"], user_id, option_index)
            
            # Check result
            assert result is True
            
            # Check that vote was recorded
            assert user_id in poll_info["votes"]
            assert poll_info["votes"][user_id] == option_index
            
            # Check that signaling server was notified
            mock_create_task.assert_called_once()
            call_args = mock_create_task.call_args[0][0]
            assert isinstance(call_args, type(mock_signaling_server._handle_poll_event()))

def test_vote_nonexistent_poll(poll_controller):
    """Test voting in a poll that doesn't exist."""
    user_id = "test-user"
    option_index = 1
    
    result = poll_controller.vote("nonexistent-poll", user_id, option_index)
    
    # Check result
    assert result is False

def test_vote_inactive_poll(poll_controller):
    """Test voting in a poll that is inactive."""
    room_id = "test-room"
    user_id = "test-user"
    option_index = 1
    
    # Create a poll and make it inactive
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], "test-creator"
        )
        poll_info["active"] = False
        
        # Try to vote
        result = poll_controller.vote(poll_info["id"], user_id, option_index)
        
        # Check result
        assert result is False
        
        # Check that no vote was recorded
        assert user_id not in poll_info["votes"]

def test_vote_invalid_option(poll_controller):
    """Test voting with an invalid option index."""
    room_id = "test-room"
    user_id = "test-user"
    invalid_option_index = 99  # Out of range
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], "test-creator"
        )
        
        # Try to vote with an invalid option
        result = poll_controller.vote(poll_info["id"], user_id, invalid_option_index)
        
        # Check result
        assert result is False
        
        # Check that no vote was recorded
        assert user_id not in poll_info["votes"]

def test_end_poll(poll_controller, mock_signaling_server):
    """Test ending a poll."""
    room_id = "test-room"
    creator_id = "test-creator"
    
    # Create a poll and add some votes
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Add votes
        poll_info["votes"] = {
            "user1": 0,  # Red
            "user2": 1,  # Green
            "user3": 1,  # Green
            "user4": 2   # Blue
        }
        
        # Reset the mocks
        mock_signaling_server._handle_poll_event.reset_mock()
        
        # End the poll
        with patch('asyncio.create_task') as mock_create_task, \
             patch('time.time', return_value=1234567900):
            
            results = poll_controller.end_poll(poll_info["id"], creator_id)
            
            # Check that poll was marked as inactive
            assert poll_info["active"] is False
            assert poll_info["ended_at"] == 1234567900
            
            # Check results
            assert results["counts"] == [1, 2, 1]  # 1 Red, 2 Green, 1 Blue
            assert results["total_votes"] == 4
            assert results["percentages"] == [25.0, 50.0, 25.0]
            
            # Check that results were stored in the poll
            assert poll_info["results"] == results
            
            # Check that signaling server was notified
            mock_create_task.assert_called_once()
            call_args = mock_create_task.call_args[0][0]
            assert isinstance(call_args, type(mock_signaling_server._handle_poll_event()))

def test_end_poll_no_votes(poll_controller):
    """Test ending a poll with no votes."""
    room_id = "test-room"
    creator_id = "test-creator"
    
    # Create a poll with no votes
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # End the poll
        with patch('asyncio.create_task'), \
             patch('time.time', return_value=1234567900):
            
            results = poll_controller.end_poll(poll_info["id"], creator_id)
            
            # Check results
            assert results["counts"] == [0, 0, 0]  # No votes
            assert results["total_votes"] == 0
            assert results["percentages"] == [0, 0, 0]

def test_end_poll_by_non_creator(poll_controller):
    """Test ending a poll by someone who is not the creator."""
    room_id = "test-room"
    creator_id = "test-creator"
    non_creator_id = "another-user"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Mock _is_admin to return False
        with patch.object(poll_controller, '_is_admin', return_value=False):
            # Try to end the poll as a non-creator and non-admin
            results = poll_controller.end_poll(poll_info["id"], non_creator_id)
            
            # Check that poll was not ended
            assert poll_info["active"] is True
            assert "ended_at" not in poll_info
            assert poll_info["results"] is None
            
            # Check results
            assert results is None

def test_end_poll_by_admin(poll_controller):
    """Test ending a poll by an admin."""
    room_id = "test-room"
    creator_id = "test-creator"
    admin_id = "admin-user"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Mock _is_admin to return True
        with patch.object(poll_controller, '_is_admin', return_value=True), \
             patch('asyncio.create_task'), \
             patch('time.time', return_value=1234567900):
            
            # End the poll as an admin
            results = poll_controller.end_poll(poll_info["id"], admin_id)
            
            # Check that poll was ended
            assert poll_info["active"] is False
            assert poll_info["ended_at"] == 1234567900
            assert poll_info["results"] is not None
            
            # Check results
            assert results is not None
            assert "counts" in results
            assert "total_votes" in results
            assert "percentages" in results

def test_get_poll_info(poll_controller):
    """Test getting poll information."""
    room_id = "test-room"
    creator_id = "test-creator"
    user_id = "test-user"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        created_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Get poll info as creator
        poll_info = poll_controller.get_poll_info(created_info["id"], creator_id)
        
        # Check that we got the same info back
        assert poll_info is created_info
        assert poll_info["id"] == "poll-123"
        assert poll_info["room_id"] == room_id
        assert poll_info["question"] == "What is your favorite color?"
        
        # Get poll info as regular user
        poll_info = poll_controller.get_poll_info(created_info["id"], user_id)
        
        # Should still get the same info since the poll is not anonymous
        assert poll_info is created_info

def test_get_anonymous_poll_info(poll_controller):
    """Test getting information about an anonymous poll."""
    room_id = "test-room"
    creator_id = "test-creator"
    user_id = "test-user"
    
    # Create an anonymous poll with some votes
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id, True
        )
        
        # Add votes
        poll_info["votes"] = {
            "user1": 0,  # Red
            "user2": 1,  # Green
            "user3": 1,  # Green
            "user4": 2   # Blue
        }
        
        # Mock _is_admin to return False
        with patch.object(poll_controller, '_is_admin', return_value=False):
            # Get poll info as regular user
            user_poll_info = poll_controller.get_poll_info(poll_info["id"], user_id)
            
            # Check that we got a copy without identifying vote information
            assert user_poll_info is not poll_info
            assert "votes" not in user_poll_info
            assert "vote_counts" in user_poll_info
            assert user_poll_info["vote_counts"] == {0: 1, 1: 2, 2: 1}
            
            # Get poll info as creator
            creator_poll_info = poll_controller.get_poll_info(poll_info["id"], creator_id)
            
            # Creator should see all information including votes
            assert creator_poll_info is poll_info
            assert "votes" in creator_poll_info
            assert creator_poll_info["votes"] == {
                "user1": 0, "user2": 1, "user3": 1, "user4": 2
            }

def test_list_active_polls(poll_controller):
    """Test listing active polls."""
    room_id = "test-room"
    other_room_id = "other-room"
    
    # Create some polls
    with patch('uuid.uuid4', side_effect=[
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-1"),
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-2"),
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-3")
        ]), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        # Create an active poll in the test room
        poll1 = poll_controller.create_poll(
            room_id, "Poll 1", ["Option A", "Option B"], "creator-1"
        )
        
        # Create an inactive poll in the test room
        poll2 = poll_controller.create_poll(
            room_id, "Poll 2", ["Option A", "Option B"], "creator-2"
        )
        poll2["active"] = False
        
        # Create an active poll in another room
        poll3 = poll_controller.create_poll(
            other_room_id, "Poll 3", ["Option A", "Option B"], "creator-3"
        )
        
        # List active polls in the test room
        active_polls = poll_controller.list_active_polls(room_id)
        
        # Check that only the active poll in the test room is listed
        assert len(active_polls) == 1
        assert active_polls[0] is poll1
        assert active_polls[0]["id"] == "poll-1"

def test_list_all_polls(poll_controller):
    """Test listing all polls."""
    room_id = "test-room"
    other_room_id = "other-room"
    
    # Create some polls
    with patch('uuid.uuid4', side_effect=[
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-1"),
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-2"),
            Mock(spec=uuid.UUID, __str__=lambda _: "poll-3")
        ]), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        # Create an active poll in the test room
        poll1 = poll_controller.create_poll(
            room_id, "Poll 1", ["Option A", "Option B"], "creator-1"
        )
        
        # Create an inactive poll in the test room
        poll2 = poll_controller.create_poll(
            room_id, "Poll 2", ["Option A", "Option B"], "creator-2"
        )
        poll2["active"] = False
        
        # Create an active poll in another room
        poll3 = poll_controller.create_poll(
            other_room_id, "Poll 3", ["Option A", "Option B"], "creator-3"
        )
        
        # List all polls in the test room
        all_polls = poll_controller.list_all_polls(room_id)
        
        # Check that both polls in the test room are listed
        assert len(all_polls) == 2
        assert poll1 in all_polls
        assert poll2 in all_polls
        assert poll3 not in all_polls

def test_delete_poll(poll_controller, mock_signaling_server):
    """Test deleting a poll."""
    room_id = "test-room"
    creator_id = "test-creator"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Reset the mocks
        mock_signaling_server._handle_poll_event.reset_mock()
        
        # Delete the poll
        with patch('asyncio.create_task') as mock_create_task:
            result = poll_controller.delete_poll(poll_info["id"], creator_id)
            
            # Check result
            assert result is True
            
            # Check that poll was removed
            assert poll_info["id"] not in poll_controller.active_polls
            
            # Check that signaling server was notified
            mock_create_task.assert_called_once()
            call_args = mock_create_task.call_args[0][0]
            assert isinstance(call_args, type(mock_signaling_server._handle_poll_event()))

def test_delete_poll_by_non_creator(poll_controller):
    """Test deleting a poll by someone who is not the creator."""
    room_id = "test-room"
    creator_id = "test-creator"
    non_creator_id = "another-user"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Mock _is_admin to return False
        with patch.object(poll_controller, '_is_admin', return_value=False):
            # Try to delete the poll as a non-creator and non-admin
            result = poll_controller.delete_poll(poll_info["id"], non_creator_id)
            
            # Check result
            assert result is False
            
            # Check that poll was not removed
            assert poll_info["id"] in poll_controller.active_polls

def test_delete_poll_by_admin(poll_controller):
    """Test deleting a poll by an admin."""
    room_id = "test-room"
    creator_id = "test-creator"
    admin_id = "admin-user"
    
    # Create a poll
    with patch('uuid.uuid4', return_value=Mock(spec=uuid.UUID, __str__=lambda _: "poll-123")), \
         patch('time.time', return_value=1234567890), \
         patch('asyncio.create_task'):
        
        poll_info = poll_controller.create_poll(
            room_id, "What is your favorite color?", ["Red", "Green", "Blue"], creator_id
        )
        
        # Mock _is_admin to return True
        with patch.object(poll_controller, '_is_admin', return_value=True), \
             patch('asyncio.create_task'):
            
            # Delete the poll as an admin
            result = poll_controller.delete_poll(poll_info["id"], admin_id)
            
            # Check result
            assert result is True
            
            # Check that poll was removed
            assert poll_info["id"] not in poll_controller.active_polls

def test_is_admin(poll_controller):
    """Test the _is_admin method."""
    # The method currently always returns False
    assert poll_controller._is_admin("user-id", "room-id") is False