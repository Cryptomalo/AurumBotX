import requests
import json

API_BASE = "http://localhost:5678"

def test_emergency_stop():
    """Test the emergency stop functionality."""
    print("--- Testing Emergency Stop ---")
    try:
        response = requests.post(f"{API_BASE}/api/emergency-stop", json={"reason": "Test from script"})
        if response.status_code == 200:
            print("✅ Emergency Stop endpoint test PASSED.")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Emergency Stop endpoint test FAILED. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception during Emergency Stop test: {e}")

if __name__ == "__main__":
    test_emergency_stop()

