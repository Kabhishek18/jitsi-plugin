# tests/e2e/setup_test_env.py

import os
import subprocess
import time
import signal
import sys

def start_test_env():
    """Start the test environment."""
    print("Starting Jitsi test environment...")
    
    # Run docker-compose up
    process = subprocess.Popen(
        ["docker-compose", "-f", "docker-compose.yml", "up", "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Error starting test environment: {stderr.decode()}")
        sys.exit(1)
    
    print("Waiting for services to start...")
    time.sleep(30)  # Wait for services to be ready
    
    # Set environment variables for tests
    os.environ["E2E_TESTS"] = "1"
    os.environ["JITSI_SERVER_TYPE"] = "self_hosted"
    os.environ["JITSI_DOMAIN"] = "localhost:8000"
    os.environ["JITSI_JWT_SECRET"] = "test-secret"
    
    print("Test environment is ready!")

def stop_test_env():
    """Stop the test environment."""
    print("Stopping Jitsi test environment...")
    
    # Run docker-compose down
    process = subprocess.Popen(
        ["docker-compose", "-f", "docker-compose.yml", "down"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Error stopping test environment: {stderr.decode()}")
        sys.exit(1)
    
    print("Test environment stopped.")

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            start_test_env()
        elif sys.argv[1] == "stop":
            stop_test_env()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python setup_test_env.py [start|stop]")
            sys.exit(1)
    else:
        # No arguments, start test environment and run tests
        try:
            start_test_env()
            
            # Run the tests
            subprocess.run(["pytest", "tests/e2e", "-v"])
            
        finally:
            # Clean up
            stop_test_env()