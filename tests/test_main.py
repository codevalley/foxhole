from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """
    Test the health check endpoint to ensure it returns a 200 status code
    and the correct JSON response.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Add more tests for other endpoints and functionalities