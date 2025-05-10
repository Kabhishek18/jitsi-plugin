# tests/integration/test_rest_api.py

import pytest
import json
from unittest.mock import patch

from jitsi_py.api.rest import JitsiRestClient
from tests.mocks.rest_responses import (
    CREATE_ROOM_RESPONSE, 
    GET_PARTICIPANTS_RESPONSE,
    START_RECORDING_RESPONSE,
    CREATE_TOKEN_RESPONSE,
    ERROR_RESPONSE
)

class TestJitsiRestClient:
    
    def test_create_room(self, jitsi_rest_client, mock_rest_api):
        """Test creating a room via the REST API."""
        mock_rest_api.post(
            "https://api.jitsi.example.com/rooms",
            json=CREATE_ROOM_RESPONSE,
            status_code=200
        )
        
        response = jitsi_rest_client.create_room(
            room_name="test-room",
            options={"audio": {"enabled": True}}
        )
        
        assert response == CREATE_ROOM_RESPONSE
        assert mock_rest_api.last_request.json() == {
            "name": "test-room",
            "options": {"audio": {"enabled": True}}
        }
        assert "ApiKey" in mock_rest_api.last_request.headers["Authorization"]
    
    def test_get_room(self, jitsi_rest_client, mock_rest_api):
        """Test getting a room via the REST API."""
        mock_rest_api.get(
            "https://api.jitsi.example.com/rooms/test-room",
            json=CREATE_ROOM_RESPONSE,
            status_code=200
        )
        
        response = jitsi_rest_client.get_room("test-room")
        
        assert response == CREATE_ROOM_RESPONSE
    
    def test_update_room(self, jitsi_rest_client, mock_rest_api):
        """Test updating a room via the REST API."""
        mock_rest_api.put(
            "https://api.jitsi.example.com/rooms/test-room",
            json=CREATE_ROOM_RESPONSE,
            status_code=200
        )
        
        response = jitsi_rest_client.update_room(
            room_name="test-room",
            options={"video": {"enabled": False}}
        )
        
        assert response == CREATE_ROOM_RESPONSE
        assert mock_rest_api.last_request.json() == {
            "options": {"video": {"enabled": False}}
        }
    
    def test_delete_room(self, jitsi_rest_client, mock_rest_api):
        """Test deleting a room via the REST API."""
        mock_rest_api.delete(
            "https://api.jitsi.example.com/rooms/test-room",
            json={"status": "deleted"},
            status_code=200
        )
        
        response = jitsi_rest_client.delete_room("test-room")
        
        assert response == {"status": "deleted"}
    
    def test_get_participants(self, jitsi_rest_client, mock_rest_api):
        """Test getting participants via the REST API."""
        mock_rest_api.get(
            "https://api.jitsi.example.com/rooms/test-room/participants",
            json=GET_PARTICIPANTS_RESPONSE,
            status_code=200
        )
        
        response = jitsi_rest_client.get_participants("test-room")
        
        assert response == GET_PARTICIPANTS_RESPONSE
    
    def test_start_recording(self, jitsi_rest_client, mock_rest_api):
        """Test starting recording via the REST API."""
        mock_rest_api.post(
            "https://api.jitsi.example.com/rooms/test-room/recording/start",
            json=START_RECORDING_RESPONSE,
            status_code=200
        )
        
        options = {
            "format": "mp4",
            "storage": "s3",
            "include_chat": True
        }
        
        response = jitsi_rest_client.start_recording("test-room", options)
        
        assert response == START_RECORDING_RESPONSE
        assert mock_rest_api.last_request.json() == options
    
    def test_stop_recording(self, jitsi_rest_client, mock_rest_api):
        """Test stopping recording via the REST API."""
        mock_rest_api.post(
            "https://api.jitsi.example.com/rooms/test-room/recording/stop",
            json={"status": "stopped"},
            status_code=200
        )
        
        response = jitsi_rest_client.stop_recording("test-room")
        
        assert response == {"status": "stopped"}
    
    def test_error_handling(self, jitsi_rest_client, mock_rest_api):
        """Test error handling for API requests."""
        mock_rest_api.get(
            "https://api.jitsi.example.com/rooms/nonexistent-room",
            json=ERROR_RESPONSE,
            status_code=404
        )
        
        with pytest.raises(Exception):
            jitsi_rest_client.get_room("nonexistent-room")
    
    def test_create_access_token(self, jitsi_rest_client, mock_rest_api):
        """Test creating an access token via the REST API."""
        mock_rest_api.post(
            "https://api.jitsi.example.com/tokens",
            json=CREATE_TOKEN_RESPONSE,
            status_code=200
        )
        
        response = jitsi_rest_client.create_access_token(
            room_name="test-room",
            user_id="test-user",
            display_name="Test User",
            email="test@example.com",
            role="host",
            expiry=3600
        )
        
        assert response == CREATE_TOKEN_RESPONSE
        assert mock_rest_api.last_request.json() == {
            "user_id": "test-user",
            "room": "test-room",
            "role": "host",
            "expiry": 3600,
            "display_name": "Test User",
            "email": "test@example.com"
        }