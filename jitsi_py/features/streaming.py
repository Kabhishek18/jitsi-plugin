# jitsi_py/features/streaming.py

from enum import Enum
from typing import Dict, Optional, List, Any

class StreamingMode(Enum):
    BROADCAST = "broadcast"  # One-way video streaming
    CONFERENCE = "conference"  # Full video conferencing

class StreamingService(Enum):
    YOUTUBE = "youtube"
    TWITCH = "twitch"
    FACEBOOK = "facebook"
    CUSTOM = "custom"

class StreamingConfig:
    """Configuration for streaming features."""
    
    def __init__(
        self,
        enabled: bool = False,
        mode: StreamingMode = StreamingMode.CONFERENCE,
        service: Optional[StreamingService] = None,
        key: Optional[str] = None,
        rtmp_url: Optional[str] = None,
        low_latency: bool = False,
        public: bool = False
    ):
        self.enabled = enabled
        self.mode = mode
        self.service = service
        self.key = key
        self.rtmp_url = rtmp_url
        self.low_latency = low_latency
        self.public = public
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        config = {
            "enableLiveStreaming": self.enabled,
            "liveStreamingMode": self.mode.value,
            "lowLatency": self.low_latency,
            "publicStream": self.public
        }
        
        if self.service:
            config["streamingService"] = self.service.value
        
        if self.service == StreamingService.CUSTOM and self.rtmp_url:
            config["rtmpUrl"] = self.rtmp_url
        
        if self.key:
            config["streamingKey"] = self.key
        
        return config