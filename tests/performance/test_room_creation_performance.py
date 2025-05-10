# tests/performance/test_room_creation_performance.py

import time
import pytest
from jitsi_py.core.client import JitsiClient

def test_room_creation_performance():
    """Test the performance of room creation."""
    client = JitsiClient()
    
    num_rooms = 100
    start_time = time.time()
    
    for i in range(num_rooms):
        room_name = f"perf-test-room-{i}"
        room = client.create_room(room_name)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Calculate metrics
    avg_time_per_room = elapsed_time / num_rooms
    rooms_per_second = num_rooms / elapsed_time
    
    print(f"Created {num_rooms} rooms in {elapsed_time:.2f} seconds")
    print(f"Average time per room: {avg_time_per_room:.4f} seconds")
    print(f"Rooms per second: {rooms_per_second:.2f}")
    
    # Assert that performance is within acceptable limits
    assert avg_time_per_room < 0.1  # Each room creation should take less than 100ms