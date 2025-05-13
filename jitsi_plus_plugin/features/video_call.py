"""
Video call controller for managing video conferencing features.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class VideoCallController:
    """
    Controller for managing video calls.
    Handles room creation, configuration, and feature toggling.
    """
    
    def __init__(self, jitsi_connector, signaling_server):
        """
        Initialize the video call controller.
        
        Args:
            jitsi_connector: Jitsi connector instance.
            signaling_server: Signaling server instance.
        """
        self.jitsi = jitsi_connector
        self.signaling = signaling_server
        self.active_calls = {}
    
    def create_call(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new video call.
        
        Args:
            config (Dict[str, Any], optional): Call configuration.
            
        Returns:
            Dict[str, Any]: Call information.
        """
        config = config or {}
        
        # Generate call ID
        call_id = str(uuid.uuid4())
        
        # Create Jitsi room
        room_info = self.jitsi.create_room(f"call-{call_id}")
        
        # Configure features
        features = config.get("features", {})
        if features:
            self.jitsi.configure_room(room_info["room_name"], features)
            # Store call information
        call_info = {
            "id": call_id,
            "room_name": room_info["room_name"],
            "jitsi_url": self.jitsi.get_jitsi_url(room_info["room_name"]),
            "created_at": room_info["created_at"],
            "features": room_info["features"],
            "max_participants": config.get("max_participants", 100),
            "participants": {},
            "recording": config.get("recording", False)
        }
        
        self.active_calls[call_id] = call_info
        
        logger.info(f"Created video call: {call_id}")
        return call_info
    
    def join_call(self, call_id: str, participant_name: str, participant_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Join a video call.
        
        Args:
            call_id (str): ID of the call to join.
            participant_name (str): Name of the participant.
            participant_config (Dict[str, Any], optional): Participant configuration.
            
        Returns:
            Dict[str, Any]: Participant information.
        """
        if call_id not in self.active_calls:
            raise ValueError(f"Call not found: {call_id}")
        
        call_info = self.active_calls[call_id]
        
        # Check if call is full
        if len(call_info["participants"]) >= call_info["max_participants"]:
            raise ValueError(f"Call is full: {call_id}")
        
        # Join Jitsi room
        participant_info = self.jitsi.join_room(call_info["room_name"], participant_name)
        
        # Configure participant features
        if participant_config:
            features = participant_config.get("features", {})
            for feature, enabled in features.items():
                self.jitsi.toggle_participant_feature(call_info["room_name"], participant_info["id"], feature, enabled)
                participant_info["features"][feature] = enabled
        
        # Add to call participants
        call_info["participants"][participant_info["id"]] = participant_info
        
        logger.info(f"Participant {participant_name} joined call {call_id}")
        return participant_info
    
    def leave_call(self, call_id: str, participant_id: str) -> bool:
        """
        Leave a video call.
        
        Args:
            call_id (str): ID of the call.
            participant_id (str): ID of the participant.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return False
        
        call_info = self.active_calls[call_id]
        
        # Leave Jitsi room
        result = self.jitsi.leave_room(call_info["room_name"], participant_id)
        
        if result:
            # Remove from call participants
            if participant_id in call_info["participants"]:
                del call_info["participants"][participant_id]
            
            # Clean up empty call
            if not call_info["participants"]:
                del self.active_calls[call_id]
                logger.info(f"Call {call_id} ended (no participants left)")
            
            logger.info(f"Participant {participant_id} left call {call_id}")
            return True
        
        return False
    
    def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a call.
        
        Args:
            call_id (str): ID of the call.
            
        Returns:
            Optional[Dict[str, Any]]: Call information or None if not found.
        """
        return self.active_calls.get(call_id)
    
    def list_active_calls(self) -> List[Dict[str, Any]]:
        """
        List all active calls.
        
        Returns:
            List[Dict[str, Any]]: List of active call information.
        """
        return list(self.active_calls.values())
    
    def toggle_call_feature(self, call_id: str, feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for a call.
        
        Args:
            call_id (str): ID of the call.
            feature (str): Feature to toggle.
            enabled (bool): Whether the feature is enabled.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return False
        
        call_info = self.active_calls[call_id]
        
        # Toggle feature in Jitsi room
        result = self.jitsi.configure_room(call_info["room_name"], {feature: enabled})
        
        if result:
            # Update call information
            call_info["features"][feature] = enabled
            
            logger.info(f"Call {call_id} feature {feature} set to {enabled}")
            return True
        
        return False
    
    def toggle_participant_feature(self, call_id: str, participant_id: str, feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for a participant.
        
        Args:
            call_id (str): ID of the call.
            participant_id (str): ID of the participant.
            feature (str): Feature to toggle.
            enabled (bool): Whether the feature is enabled.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return False
        
        call_info = self.active_calls[call_id]
        
        # Toggle feature for participant
        result = self.jitsi.toggle_participant_feature(call_info["room_name"], participant_id, feature, enabled)
        
        if result:
            # Update participant information
            if participant_id in call_info["participants"]:
                call_info["participants"][participant_id]["features"][feature] = enabled
            
            logger.info(f"Participant {participant_id} feature {feature} set to {enabled} in call {call_id}")
            return True
        
        return False
    
    def start_recording(self, call_id: str) -> bool:
        """
        Start recording a call.
        
        Args:
            call_id (str): ID of the call.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # This method would integrate with the media server to start recording
        # the call via RTMP or other methods
        # For now, just update the call state
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return False
        
        self.active_calls[call_id]["recording"] = True
        logger.info(f"Started recording call: {call_id}")
        return True
    
    def stop_recording(self, call_id: str) -> bool:
        """
        Stop recording a call.
        
        Args:
            call_id (str): ID of the call.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # This method would integrate with the media server to stop recording
        # For now, just update the call state
        if call_id not in self.active_calls:
            logger.warning(f"Call not found: {call_id}")
            return False
        
        self.active_calls[call_id]["recording"] = False
        logger.info(f"Stopped recording call: {call_id}")
        return True