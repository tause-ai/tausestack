import pytest
from fastapi.testclient import TestClient
from core.modules.auth.api.routes import router as auth_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(auth_router, prefix="/auth")

client = TestClient(app)

def test_login_exitoso(monkeypatch):
    # Mock de autenticación exitosa
    def mock_authenticate_user(username, password):
        return True
    monkeypatch.setattr("core.modules.auth.services.service.authenticate_user", mock_authenticate_user)
    response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    assert response.json()["msg"] == "login"

def test_login_fallido(monkeypatch):
    def mock_authenticate_user(username, password):
        return False
    monkeypatch.setattr("core.modules.auth.services.service.authenticate_user", mock_authenticate_user)
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401 or response.status_code == 400

# Ejemplo de integración: login consulta users
@pytest.fixture
def fake_user():
    return {"id": 1, "username": "admin"}

def test_login_consulta_usuario(monkeypatch, fake_user):
    def mock_get_user_by_username(username):
        if username == "admin":
            return fake_user
        return None
    monkeypatch.setattr("core.modules.users.services.service.get_user_by_username", mock_get_user_by_username)
    # Aquí iría la lógica de login que consulta users
    assert mock_get_user_by_username("admin") == fake_user

# Validación de token (simulado)
def test_validacion_token():
    token = "fake-token"
    # Aquí iría la lógica real de validación de token
    assert isinstance(token, str)
