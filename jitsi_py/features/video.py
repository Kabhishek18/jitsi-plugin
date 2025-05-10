# jitsi_py/features/video.py

from typing import Dict, Optional, List, Any
from enum import Enum

class VideoQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HD = "hd"

class VideoConfig:
    """Configuration for video features."""
    
    def __init__(
        self,
        enabled: bool = True,
        muted: bool = False,
        auto_mute_on_join: bool = False,
        quality: VideoQuality = VideoQuality.MEDIUM,
        background_blur: bool = False,
        virtual_background: Optional[str] = None,
        device_id: Optional[str] = None
    ):
        self.enabled = enabled
        self.muted = muted
        self.auto_mute_on_join = auto_mute_on_join
        self.quality = quality
        self.background_blur = background_blur
        self.virtual_background = virtual_background
        self.device_id = device_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        config = {
            "startWithVideoMuted": self.muted or self.auto_mute_on_join,
            "disableVideo": not self.enabled,
            "resolution": self._get_resolution(),
            "videoDeviceId": self.device_id
        }
        
        if self.background_blur:
            config["backgroundBlur"] = True
        
        if self.virtual_background:
            config["virtualBackground"] = self.virtual_background
        
        return config
    
    def _get_resolution(self) -> int:
        """Get the resolution based on the quality."""
        resolutions = {
            VideoQuality.LOW: 180,
            VideoQuality.MEDIUM: 360,
            VideoQuality.HIGH: 720,
            VideoQuality.HD: 1080
        }
        
        return resolutions[self.quality]

