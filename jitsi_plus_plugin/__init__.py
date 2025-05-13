"""
Jitsi Plus Plugin - A comprehensive communication solution built on Jitsi
with video conferencing, audio calls, broadcasting, and VOD capabilities.
"""

__version__ = '0.1.0'

from .core.jitsi_connector import JitsiConnector
from .core.media_server import MediaServer
from .core.signaling import SignalingServer

from .features.video_call import VideoCallController
from .features.audio_call import AudioCallController
from .features.broadcast import BroadcastController
from .features.vod import VideoOnDemand
from .features.whiteboard import WhiteboardController
from .features.polls import PollController

class JitsiPlusPlugin:
    """Main plugin class that integrates all components."""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # Initialize core components
        self.jitsi = JitsiConnector(self.config.get("jitsi", {}))
        self.media_server = MediaServer(self.config.get("media_server", {}))
        self.signaling = SignalingServer(self.config.get("signaling", {}))
        
        # Initialize features
        self.video_call = VideoCallController(self.jitsi, self.signaling)
        self.audio_call = AudioCallController(self.jitsi, self.signaling)
        self.broadcast = BroadcastController(self.jitsi, self.media_server, self.signaling)
        self.vod = VideoOnDemand(self.media_server)
        self.whiteboard = WhiteboardController(self.signaling)
        self.polls = PollController(self.signaling)
    
    def initialize(self):
        """Initialize all components and start the plugin."""
        # Initialize core components
        self.jitsi.initialize()
        self.media_server.initialize()
        self.signaling.start()
        
        return {
            "status": "initialized",
            "version": __version__,
            "features": {
                "video_call": True,
                "audio_call": True,
                "broadcast": True,
                "vod": True,
                "whiteboard": True,
                "polls": True
            }
        }
    
    def shutdown(self):
        """Properly shutdown all components."""
        self.signaling.stop()
        self.media_server.shutdown()
        self.jitsi.disconnect()
        
        return {"status": "shutdown"}