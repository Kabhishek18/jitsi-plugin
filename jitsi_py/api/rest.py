# jitsi_py/api/rest.py

import requests
import json
import logging
from typing import Dict, Optional, List, Any, Union

class JitsiRestClient:
    """Client for interacting with Jitsi REST API."""
    
    def __init__(
        self,
        api_endpoint: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None
    ):
        """Initialize the REST client.
        
        Args:
            api_endpoint: Endpoint for the Jitsi REST API.
            api_key: API key for authentication.
            jwt_token: JWT token for authentication.
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.logger = logging.getLogger("jitsi_py.api.rest")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests.
        
        Returns:
            Headers dictionary.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        elif self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make an API request.
        
        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request data.
            params: Query parameters.
            
        Returns:
            Response data.
        """
        url = f"{self.api_endpoint}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    self.logger.error(f"API error response: {json.dumps(error_data)}")
                except:
                    self.logger.error(f"API error status: {e.response.status_code}")
            raise
    
    def create_room(
        self,
        room_name: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Create a new room.
        
        Args:
            room_name: Name of the room.
            options: Room options.
            
        Returns:
            Room data.
        """
        data = {
            "name": room_name,
            "options": options or {}
        }
        
        return self._make_request("POST", "/rooms", data=data)
    
    def get_room(self, room_name: str) -> Dict:
        """Get a room by name.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Room data.
        """
        return self._make_request("GET", f"/rooms/{room_name}")
    
    def update_room(
        self,
        room_name: str,
        options: Dict
    ) -> Dict:
        """Update a room.
        
        Args:
            room_name: Name of the room.
            options: Room options.
            
        Returns:
            Updated room data.
        """
        return self._make_request("PUT", f"/rooms/{room_name}", data={"options": options})
    
    def delete_room(self, room_name: str) -> Dict:
        """Delete a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Response data.
        """
        return self._make_request("DELETE", f"/rooms/{room_name}")
    
    def get_participants(self, room_name: str) -> List[Dict]:
        """Get participants in a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            List of participants.
        """
        return self._make_request("GET", f"/rooms/{room_name}/participants")
    
    def kick_participant(
        self,
        room_name: str,
        participant_id: str
    ) -> Dict:
        """Kick a participant from a room.
        
        Args:
            room_name: Name of the room.
            participant_id: ID of the participant.
            
        Returns:
            Response data.
        """
        return self._make_request(
            "DELETE", 
            f"/rooms/{room_name}/participants/{participant_id}"
        )
    
    def mute_participant(
        self,
        room_name: str,
        participant_id: str,
        mute_audio: bool = True,
        mute_video: bool = False
    ) -> Dict:
        """Mute a participant.
        
        Args:
            room_name: Name of the room.
            participant_id: ID of the participant.
            mute_audio: Whether to mute audio.
            mute_video: Whether to mute video.
            
        Returns:
            Response data.
        """
        data = {
            "mute_audio": mute_audio,
            "mute_video": mute_video
        }
        
        return self._make_request(
            "POST", 
            f"/rooms/{room_name}/participants/{participant_id}/mute",
            data=data
        )
    
    def start_recording(
        self,
        room_name: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Start recording a room.
        
        Args:
            room_name: Name of the room.
            options: Recording options.
            
        Returns:
            Recording data.
        """
        return self._make_request(
            "POST", 
            f"/rooms/{room_name}/recording/start",
            data=options
        )
    
    def stop_recording(self, room_name: str) -> Dict:
        """Stop recording a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Response data.
        """
        return self._make_request("POST", f"/rooms/{room_name}/recording/stop")
    
    def get_recordings(self, room_name: str) -> List[Dict]:
        """Get recordings for a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            List of recordings.
        """
        return self._make_request("GET", f"/rooms/{room_name}/recordings")
    
    def delete_recording(
        self,
        room_name: str,
        recording_id: str
    ) -> Dict:
        """Delete a recording.
        
        Args:
            room_name: Name of the room.
            recording_id: ID of the recording.
            
        Returns:
            Response data.
        """
        return self._make_request(
            "DELETE", 
            f"/rooms/{room_name}/recordings/{recording_id}"
        )
    
    def start_streaming(
        self,
        room_name: str,
        options: Dict
    ) -> Dict:
        """Start streaming a room.
        
        Args:
            room_name: Name of the room.
            options: Streaming options.
            
        Returns:
            Streaming data.
        """
        return self._make_request(
            "POST", 
            f"/rooms/{room_name}/streaming/start",
            data=options
        )
    
    def stop_streaming(self, room_name: str) -> Dict:
        """Stop streaming a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Response data.
        """
        return self._make_request("POST", f"/rooms/{room_name}/streaming/stop")
    
    def get_streaming_status(self, room_name: str) -> Dict:
        """Get streaming status for a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Streaming status.
        """
        return self._make_request("GET", f"/rooms/{room_name}/streaming/status")
    
    def create_breakout_room(
        self,
        parent_room: str,
        room_name: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Create a breakout room.
        
        Args:
            parent_room: Name of the parent room.
            room_name: Name of the breakout room.
            options: Room options.
            
        Returns:
            Breakout room data.
        """
        data = {
            "name": room_name,
            "options": options or {}
        }
        
        return self._make_request(
            "POST", 
            f"/rooms/{parent_room}/breakout",
            data=data
        )
    
    def close_breakout_rooms(self, parent_room: str) -> Dict:
        """Close all breakout rooms for a parent room.
        
        Args:
            parent_room: Name of the parent room.
            
        Returns:
            Response data.
        """
        return self._make_request("DELETE", f"/rooms/{parent_room}/breakout")
    
    def send_message(
        self,
        room_name: str,
        message: str,
        to: Optional[str] = None
    ) -> Dict:
        """Send a message to a room.
        
        Args:
            room_name: Name of the room.
            message: Message text.
            to: Recipient ID (optional, for direct messages).
            
        Returns:
            Response data.
        """
        data = {
            "message": message
        }
        
        if to:
            data["to"] = to
        
        return self._make_request(
            "POST", 
            f"/rooms/{room_name}/message",
            data=data
        )
    
    def get_transcription(
        self,
        room_name: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Get transcription for a room.
        
        Args:
            room_name: Name of the room.
            options: Transcription options.
            
        Returns:
            Transcription data.
        """
        return self._make_request(
            "GET", 
            f"/rooms/{room_name}/transcription",
            params=options
        )
    
    def start_transcription(
        self,
        room_name: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Start transcription for a room.
        
        Args:
            room_name: Name of the room.
            options: Transcription options.
            
        Returns:
            Response data.
        """
        return self._make_request(
            "POST", 
            f"/rooms/{room_name}/transcription/start",
            data=options
        )
    
    def stop_transcription(self, room_name: str) -> Dict:
        """Stop transcription for a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Response data.
        """
        return self._make_request("POST", f"/rooms/{room_name}/transcription/stop")
    
    def create_access_token(
        self,
        room_name: str,
        user_id: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = "viewer",
        expiry: Optional[int] = 3600
    ) -> Dict:
        """Create an access token for a room.
        
        Args:
            room_name: Name of the room.
            user_id: ID of the user.
            display_name: Display name of the user.
            email: Email of the user.
            role: Role of the user.
            expiry: Token expiry time in seconds.
            
        Returns:
            Token data.
        """
        data = {
            "user_id": user_id,
            "room": room_name,
            "role": role,
            "expiry": expiry
        }
        
        if display_name:
            data["display_name"] = display_name
        
        if email:
            data["email"] = email
        
        return self._make_request("POST", "/tokens", data=data)
    
    def get_room_statistics(self, room_name: str) -> Dict:
        """Get statistics for a room.
        
        Args:
            room_name: Name of the room.
            
        Returns:
            Room statistics.
        """
        return self._make_request("GET", f"/rooms/{room_name}/stats")
    
    def get_server_health(self) -> Dict:
        """Get server health status.
        
        Returns:
            Server health status.
        """
        return self._make_request("GET", "/health")
    
    def get_server_config(self) -> Dict:
        """Get server configuration.
        
        Returns:
            Server configuration.
        """
        return self._make_request("GET", "/config")