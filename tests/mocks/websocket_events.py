# tests/mocks/websocket_events.py

# Sample WebSocket events
PARTICIPANT_JOINED_EVENT = {
    "type": "participant_joined",
    "data": {
        "room_name": "test-room",
        "participant": {
            "id": "participant3",
            "display_name": "Test User 3",
            "role": "viewer",
            "joined_at": "2023-09-01T12:15:00Z"
        }
    }
}

PARTICIPANT_LEFT_EVENT = {
    "type": "participant_left",
    "data": {
        "room_name": "test-room",
        "participant_id": "participant2"
    }
}

RECORDING_STARTED_EVENT = {
    "type": "recording_started",
    "data": {
        "room_name": "test-room",
        "recording_id": "recording1",
        "start_time": "2023-09-01T12:10:00Z"
    }
}

CHAT_MESSAGE_EVENT = {
    "type": "chat_message",
    "data": {
        "room_name": "test-room",
        "from": {
            "id": "participant1",
            "display_name": "Test User 1"
        },
        "message": "Hello everyone!",
        "timestamp": "2023-09-01T12:20:00Z"
    }
}