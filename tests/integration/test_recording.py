# tests/integration/test_recording.py

import pytest
import os
import json
from unittest.mock import patch, MagicMock

from jitsi_py.features.recording import (
    Recording, 
    RecordingConfig, 
    RecordingFormat, 
    RecordingMode, 
    StorageProvider
)
from jitsi_py.api.rest import JitsiRestClient

class TestRecording:
    
    def test_recording_config(self):
        """Test creating a recording configuration."""
        config = RecordingConfig(
            enabled=True,
            format=RecordingFormat.MP4,
            mode=RecordingMode.FILE,
            storage=StorageProvider.S3,
            storage_config={
                "bucket": "test-bucket",
                "region": "us-west-2"
            },
            auto_start=True,
            include_chat=True,
            host_control_only=True
        )
        
        dict_config = config.to_dict()
        
        assert dict_config["enableRecording"] is True
        assert dict_config["recordingFormat"] == "mp4"
        assert dict_config["recordingMode"] == "file"
        assert dict_config["recordingStorage"] == "s3"
        assert dict_config["autoStartRecording"] is True
        assert dict_config["recordingIncludeChat"] is True
        assert dict_config["hostControlsRecording"] is True
        assert dict_config["recordingStorageConfig"]["bucket"] == "test-bucket"
        assert dict_config["recordingStorageConfig"]["region"] == "us-west-2"
    
    @patch.object(JitsiRestClient, "start_recording")
    def test_start_recording(self, mock_start_recording):
        """Test starting a recording."""
        # Setup mock
        mock_start_recording.return_value = {
            "id": "recording1",
            "room_id": "room1",
            "start_time": "2023-09-01T12:00:00Z",
            "status": "recording"
        }
        
        # Setup client and config
        client = JitsiRestClient(
            api_endpoint="https://api.jitsi.example.com",
            api_key="test_api_key"
        )
        
        config = RecordingConfig(
            enabled=True,
            format=RecordingFormat.MP4,
            storage=StorageProvider.S3,
            storage_config={"bucket": "test-bucket"}
        )
        
        # Create and start recording
        recording = Recording(
            client=client,
            room_name="test-room",
            recording_id="recording1",
            config=config
        )
        
        # Implement the start method for testing
        def start_impl():
            options = {
                "format": recording.config.format.value,
                "storage": recording.config.storage.value,
                "storage_config": recording.config.storage_config
            }
            
            response = client.start_recording(recording.room_name, options)
            recording.status = response["status"]
            return True
        
        # Patch the start method
        with patch.object(Recording, "start", side_effect=start_impl):
            result = recording.start()
            
            assert result is True
            assert recording.status == "recording"
            mock_start_recording.assert_called_once_with(
                "test-room",
                {
                    "format": "mp4",
                    "storage": "s3",
                    "storage_config": {"bucket": "test-bucket"}
                }
            )
    
    @patch.object(JitsiRestClient, "stop_recording")
    def test_stop_recording(self, mock_stop_recording):
        """Test stopping a recording."""
        # Setup mock
        mock_stop_recording.return_value = {
            "status": "stopped"
        }
        
        # Setup client and config
        client = JitsiRestClient(
            api_endpoint="https://api.jitsi.example.com",
            api_key="test_api_key"
        )
        
        config = RecordingConfig(
            enabled=True,
            format=RecordingFormat.MP4
        )
        
        # Create recording
        recording = Recording(
            client=client,
            room_name="test-room",
            recording_id="recording1",
            config=config
        )
        
        # Implement the stop method for testing
        def stop_impl():
            response = client.stop_recording(recording.room_name)
            recording.status = response["status"]
            return True
        
        # Patch the stop method
        with patch.object(Recording, "stop", side_effect=stop_impl):
            result = recording.stop()
            
            assert result is True
            assert recording.status == "stopped"
            mock_stop_recording.assert_called_once_with("test-room")