# jitsi_py/utils/url.py

from typing import Dict, Optional, List, Any
import urllib.parse

def build_jitsi_url(
    domain: str,
    room_name: str,
    token: Optional[str] = None,
    features: Optional[Dict] = None
) -> str:
    """Build a URL for joining a Jitsi room.
    
    Args:
        domain: Jitsi domain.
        room_name: Name of the room.
        token: JWT token for authentication.
        features: Features to enable.
        
    Returns:
        URL for joining the room.
    """
    # Remove protocol from domain if present
    if "://" in domain:
        domain = domain.split("://")[1]
    
    # Create the base URL
    base_url = f"https://{domain}/{room_name}"
    
    # Add query parameters
    params = {}
    
    if token:
        params["jwt"] = token
    
    if features:
        # Add feature-specific parameters
        for key, value in _convert_features_to_params(features).items():
            params[key] = value
    
    # Build the final URL
    if params:
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}#{query_string}"
    
    return base_url

def _convert_features_to_params(features: Dict) -> Dict:
    """Convert feature configurations to URL parameters.
    
    Args:
        features: Feature configurations.
        
    Returns:
        Dictionary of URL parameters.
    """
    params = {}
    
    # Audio configurations
    if "audio" in features:
        audio_config = features["audio"]
        if isinstance(audio_config, dict):
            if audio_config.get("muted"):
                params["config.startWithAudioMuted"] = "true"
            if not audio_config.get("enabled", True):
                params["config.disableAudioLevels"] = "true"
    
    # Video configurations
    if "video" in features:
        video_config = features["video"]
        if isinstance(video_config, dict):
            if video_config.get("muted"):
                params["config.startWithVideoMuted"] = "true"
            if not video_config.get("enabled", True):
                params["config.disableVideo"] = "true"
    
    # Streaming configurations
    if "streaming" in features:
        streaming_config = features["streaming"]
        if isinstance(streaming_config, dict):
            if streaming_config.get("enabled"):
                params["config.enableLiveStreaming"] = "true"
    
    # Recording configurations
    if "recording" in features:
        recording_config = features["recording"]
        if isinstance(recording_config, dict):
            if recording_config.get("enabled"):
                params["config.enableRecording"] = "true"
    
    # UI configurations
    ui_config = features.get("ui", {})
    
    # Toolbar buttons
    buttons_to_hide = ui_config.get("hide_buttons", [])
    if buttons_to_hide:
        params["config.toolbarButtons"] = ",".join([
            button for button in [
                "microphone", "camera", "closedcaptions", "desktop", 
                "fullscreen", "fodeviceselection", "hangup", "profile", 
                "chat", "recording", "livestreaming", "etherpad", 
                "sharedvideo", "settings", "raisehand", "videoquality", 
                "filmstrip", "invite", "feedback", "stats", "shortcuts", 
                "tileview", "videobackgroundblur", "download", "help", 
                "mute-everyone", "security"
            ] if button not in buttons_to_hide
        ])
    
    # Room configurations
    if "room" in features:
        room_config = features["room"]
        if isinstance(room_config, dict):
            if room_config.get("protected"):
                params["config.requirePassword"] = "true"
            if room_config.get("password"):
                params["config.password"] = room_config["password"]
            if room_config.get("lobby_enabled"):
                params["config.enableLobby"] = "true"
    
    return params