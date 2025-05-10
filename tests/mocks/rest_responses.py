# tests/mocks/rest_responses.py

# Sample responses for REST API calls
CREATE_ROOM_RESPONSE = {
    "id": "abcd1234",
    "name": "test-room",
    "created_at": "2023-09-01T12:00:00Z",
    "features": {
        "audio": {
            "enabled": True,
            "muted": False
        },
        "video": {
            "enabled": True,
            "muted": False
        }
    },
    "status": "active"
}

GET_PARTICIPANTS_RESPONSE = [
    {
        "id": "participant1",
        "display_name": "Test User 1",
        "role": "host",
        "joined_at": "2023-09-01T12:05:00Z",
        "audio_muted": False,
        "video_muted": False
    },
    {
        "id": "participant2",
        "display_name": "Test User 2",
        "role": "viewer",
        "joined_at": "2023-09-01T12:07:00Z",
        "audio_muted": True,
        "video_muted": True
    }
]

START_RECORDING_RESPONSE = {
    "id": "recording1",
    "room_id": "abcd1234",
    "start_time": "2023-09-01T12:10:00Z",
    "status": "recording",
    "format": "mp4"
}

CREATE_TOKEN_RESPONSE = {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-09-01T13:00:00Z"
}

ERROR_RESPONSE = {
    "error": "room_not_found",
    "message": "The requested room does not exist"
}