#!/usr/bin/env python3
"""
Test script for the update-messages endpoint
"""
import httpx
import json
import asyncio
import threading
import time


# API endpoint
ENDPOINT_URL = "http://localhost:8000/update-messages"

async def update_messages_async():
    """Test the update-messages endpoint"""

    # Test data as per your requirement
    test_data = {
        "request_id": "6c871bee-4175-44b6-8e83-8c881daef3b6",
        "agent_metadata": {
            "agent_name": "test_agent009",
            "agent_user_id": "chat-user-123",
            "agent_version": "1.0.0",
            "agent_app_name": "Virtusa Customer Support",
            "agent_session_id": "test-session-123"
        }
    }

    print(f"URL: {ENDPOINT_URL}")
    print(f"Payload: {json.dumps(test_data, indent=2)}")
    print("-" * 50)

    try:
        # Send POST request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ENDPOINT_URL,
                json=test_data,
                headers={"Content-Type": "application/json"}
            )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ SUCCESS: Messages updated successfully")
        elif response.status_code == 404:
            print("⚠️  Request ID not found - this is expected for test data")
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")

    except httpx.ConnectError:
        print("❌ CONNECTION ERROR: Make sure the API is running on localhost:8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def log_meta_with_background_task():
    # Run async function in separate thread
    def run_async_in_thread():
        asyncio.run(update_messages_async())

    thread = threading.Thread(target=run_async_in_thread)
    thread.start()

if __name__ == "__main__":

    log_meta_with_background_task()
    # Give background thread time to finish
    time.sleep(1)
    print("Script completed.")