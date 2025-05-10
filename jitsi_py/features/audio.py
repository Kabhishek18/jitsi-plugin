# jitsi_py/features/audio.py

from typing import Dict, Optional, List, Any

class AudioConfig:
    """Configuration for audio features."""
    
    def __init__(
        self,
        enabled: bool = True,
        muted: bool = False,
        auto_mute_on_join: bool = False,
        noise_suppression: bool = True,
        device_id: Optional[str] = None
    ):
        self.enabled = enabled
        self.muted = muted
        self.auto_mute_on_join = auto_mute_on_join
        self.noise_suppression = noise_suppression
        self.device_id = device_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        return {
            "startWithAudioMuted": self.muted or self.auto_mute_on_join,
            "disableAudioLevels": not self.enabled,
            "enableNoiseSuppressionFeature": self.noise_suppression,
            "audioDeviceId": self.device_id
        }

