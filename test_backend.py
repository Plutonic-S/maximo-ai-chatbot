import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    print("--- 1. Health Check Test ---")
    response = client.get("/")
    print("Health response:", response.json())
    assert response.status_code == 200

    print("\n--- 2. Chitchat Query Test ---")
    time.sleep(3)
    response = client.post("/api/chat", json={"message": "Hello, what can you do for me?"})
    print("Chitchat status:", response.status_code)
    print("Chitchat reply:", response.json())

    print("\n--- 3. Maximo Service Request Query Test ---")
    time.sleep(5)
    response = client.post("/api/chat", json={"message": "Are there any service request tickets for location LOC-102?"})
    print("SR Query status:", response.status_code)
    print("SR Query reply:", response.json())

    print("\n--- 4. Maximo Location Query Test ---")
    time.sleep(5)
    response = client.post("/api/chat", json={"message": "Search for Maximo locations matching site BEDFORD or query Building"})
    print("Location Query status:", response.status_code)
    print("Location Query reply:", response.json())

if __name__ == "__main__":
    run_tests()
