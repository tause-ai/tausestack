from fastapi.testclient import TestClient
from main import app

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"].lower().startswith("bienvenido")
