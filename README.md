# Jitsi Plus Plugin

[![PyPI version](https://img.shields.io/pypi/v/jitsi-plus-plugin.svg)](https://pypi.org/project/jitsi-plus-plugin/)
[![Python versions](https://img.shields.io/pypi/pyversions/jitsi-plus-plugin.svg)](https://pypi.org/project/jitsi-plus-plugin/)
[![License](https://img.shields.io/github/license/Kabhishek18/jitsi-plus-plugin.svg)](https://github.com/Kabhishek18/jitsi-plus-plugin/blob/main/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/jitsi-plus-plugin/badge/?version=latest)](https://jitsi-plus-plugin.readthedocs.io/en/latest/?badge=latest)

A comprehensive Python integration for Jitsi Meet with video conferencing, audio calls, broadcasting, and video-on-demand capabilities. This plugin provides a complete solution for building real-time communication applications.

## Features

- **Video Conferencing**
  - Host-configurable room size
  - Enable/disable video, audio, chat, and screen sharing
  - Whiteboard functionality
  - Polls and Q&A
  - Background customization
  - Settings management

- **Audio Calls**
  - Host-configurable room size
  - Enable/disable features
  - Chat integration
  - Poll functionality

- **Broadcasting**
  - Live streaming with RTMP/HLS
  - Host controls
  - Chat integration
  - Recording capabilities
  - Scales to millions of viewers

- **Video on Demand (VOD)**
  - Video player
  - URL-based playback
  - Advertisement support (pre-roll, mid-roll, post-roll)
  - High scalability (10M+ users)

## Installation

```bash
# Basic installation
pip install jitsi-plus-plugin

# With all extras
pip install jitsi-plus-plugin[all]

# With specific features
pip install jitsi-plus-plugin[media,scaling]
```

## Quick Start

### Basic Video Call

```python
from jitsi_plus_plugin import JitsiPlusPlugin

# Initialize the plugin
plugin = JitsiPlusPlugin()
plugin.initialize()

# Create a video call
call_info = plugin.video_call.create_call({
    "max_participants": 10,
    "features": {
        "video": True,
        "audio": True,
        "chat": True,
        "whiteboard": True
    }
})

print(f"Video call created: {call_info['id']}")
print(f"Join URL: {call_info['jitsi_url']}")
```

### Setting Up a Broadcast

```python
from jitsi_plus_plugin import JitsiPlusPlugin

# Initialize the plugin
plugin = JitsiPlusPlugin()
plugin.initialize()

# Create a broadcast
broadcast = plugin.broadcast.create_broadcast("My Broadcast", {
    "max_hosts": 3,
    "features": {
        "chat": True,
        "screen_sharing": True
    }
})

# Start broadcasting
plugin.broadcast.start_broadcast(broadcast["id"])

print(f"Broadcast URL: {broadcast['hls_url']}")
```

### Video on Demand with Ads

```python
from jitsi_plus_plugin import JitsiPlusPlugin

# Initialize the plugin
plugin = JitsiPlusPlugin()
plugin.initialize()

# Create VOD entry
vod = plugin.vod.create_vod_entry("My Video", "/path/to/video.mp4")

# Configure ads
plugin.vod.configure_ad_settings(vod["id"], {
    "pre_roll": ["https://example.com/ads/pre_roll.mp4"],
    "mid_roll": [
        {"time": 300, "url": "https://example.com/ads/mid_roll1.mp4"},
        {"time": 600, "url": "https://example.com/ads/mid_roll2.mp4"}
    ],
    "post_roll": ["https://example.com/ads/post_roll.mp4"]
})

# Get player configuration
player_config = plugin.vod.create_player_config(vod_id=vod["id"])
print(player_config)
```

## Complete Example

```python
import asyncio
import logging
from jitsi_plus_plugin import JitsiPlusPlugin

# Configure logging
logging.basicConfig(level=logging.INFO)

# Plugin configuration
config = {
    "jitsi": {
        "server_url": "https://meet.jit.si",
        "room_prefix": "jitsi-plus-"
    },
    "media_server": {
        "server_url": "https://media.example.com",
        "rtmp_port": 1935
    },
    "signaling": {
        "host": "0.0.0.0",
        "port": 8080
    }
}

# Initialize the plugin
plugin = JitsiPlusPlugin(config)
plugin.initialize()

# Create a video call
video_call = plugin.video_call.create_call({
    "max_participants": 10,
    "features": {
        "video": True,
        "audio": True,
        "chat": True,
        "whiteboard": True,
        "polls": True
    }
})

print(f"Video call created: {video_call['id']}")
print(f"Jitsi URL: {video_call['jitsi_url']}")

# Join the call as host
host = plugin.video_call.join_call(
    video_call["id"], 
    "Host User", 
    {"features": {"screen_sharing": True}}
)

# Enable whiteboard
plugin.whiteboard.create_whiteboard(video_call["id"])

# Create a poll
poll = plugin.polls.create_poll(
    video_call["id"],
    "What feature do you like the most?",
    ["Video", "Audio", "Chat", "Whiteboard", "Polls"],
    host["id"]
)

# Run the plugin (this will block)
try:
    # Keep the main thread alive
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    # Shutdown on Ctrl+C
    plugin.shutdown()
```

## Framework Integration

### Django Integration

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'jitsi_plus_plugin.integrations.django',
    # ...
]

JITSI_PLUS_CONFIG = {
    "jitsi": {
        "server_url": "https://meet.jit.si"
    },
    # More configuration...
}
```

### Flask Integration

```python
from flask import Flask
from jitsi_plus_plugin.integrations.flask import init_jitsi_plus

app = Flask(__name__)
jitsi_plus = init_jitsi_plus(app, {
    "jitsi": {
        "server_url": "https://meet.jit.si"
    }
})

@app.route('/create-meeting')
def create_meeting():
    meeting = jitsi_plus.video_call.create_call()
    return {"meeting_url": meeting["jitsi_url"]}
```

### FastAPI Integration

```python
from fastapi import FastAPI
from jitsi_plus_plugin.integrations.fastapi import JitsiPlusRouter

app = FastAPI()
jitsi_router = JitsiPlusRouter({
    "jitsi": {
        "server_url": "https://meet.jit.si"
    }
})

app.include_router(jitsi_router, prefix="/api/jitsi")
```

## Advanced Configuration

The plugin provides extensive configuration options to customize behavior for different environments and use cases.

```python
config = {
    "jitsi": {
        "server_url": "https://meet.jit.si",
        "room_prefix": "jitsi-plus-",
        "use_ssl": True
    },
    "media_server": {
        "server_url": "https://media.example.com",
        "rtmp_port": 1935,
        "hls_segment_duration": 4,
        "recording_enabled": True,
        "recording_directory": "/var/recordings"
    },
    "signaling": {
        "host": "0.0.0.0",
        "port": 8080,
        "use_ssl": True,
        "ssl_cert": "/path/to/cert.pem",
        "ssl_key": "/path/to/key.pem"
    },
    "scaling": {
        "auto_scaling": True,
        "max_participants_per_server": 100,
        "monitor_interval_seconds": 30
    },
    "features": {
        "whiteboard_enabled": True,
        "polls_enabled": True,
        "chat_enabled": True,
        "recording_enabled": True,
        "transcription_enabled": False
    }
}
```

## Authentication & Security

The plugin supports various authentication methods to secure your communications:

```python
# JWT authentication
from jitsi_plus_plugin.utils.auth import generate_jwt_token

token = generate_jwt_token({
    "room": "*",
    "user": {
        "name": "John Doe",
        "email": "john@example.com",
        "avatar": "https://example.com/avatar.jpg"
    },
    "exp": int(time.time()) + 86400  # 24 hours
}, "your-secret-key")

# Use token for authentication
plugin = JitsiPlusPlugin({
    "jitsi": {
        "server_url": "https://meet.jit.si",
        "jwt_token": token
    }
})
```

## Command Line Interface

The package includes a command-line interface for common operations:

```bash
# Create a video call
jitsi-plus create-call --max-participants 10 --features video audio chat

# Start a broadcast
jitsi-plus create-broadcast "Weekly Update" --record

# List active calls
jitsi-plus list-calls

# Start a media server
jitsi-plus start-media-server
```

## Cloud Deployment

The plugin supports deployment to various cloud providers:

```python
from jitsi_plus_plugin.utils.cloud import deploy_to_aws

# Deploy to AWS
deployment = deploy_to_aws({
    "region": "us-west-2",
    "instance_type": "t3.large",
    "scaling": {
        "min_instances": 1,
        "max_instances": 10,
        "target_cpu_utilization": 70
    }
})
```

## Scaling to Millions

For large-scale deployments, use the scaling utilities:

```python
from jitsi_plus_plugin.utils.scaling import setup_scaling

# Configure scaling for 10M+ users
scaling_config = setup_scaling({
    "media_servers": {
        "initial_count": 3,
        "max_count": 20,
        "auto_scale": True
    },
    "jitsi_servers": {
        "initial_count": 5,
        "max_count": 30,
        "auto_scale": True
    },
    "cdn_integration": {
        "provider": "cloudfront",
        "distribution_id": "E1EXAMPLE"
    }
})
```

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

Please make sure to update tests as appropriate.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed by Kumar Abhishek ([@Kabhishek18](https://github.com/Kabhishek18))