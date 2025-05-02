from fastapi.testclient import TestClient
from services.users.api.main import app
from shared.models import User, Organization, Permission
import uuid

def test_register_and_login_and_access():
    client = TestClient(app)
    user_id = str(uuid.uuid4())
    email = "testjwt@example.com"
    password = "strongpass123"
    user = {
        "id": user_id,
        "email": email,
        "full_name": "Test JWT User",
        "is_active": True,
        "organization_id": None,
        "roles": []
    }
    # Registro
    resp = client.post("/api/v1/auth/register", params={"password": password}, json=user)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # Login y obtención de token
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    # Acceso protegido: listar usuarios
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(u["id"] == user_id for u in resp.json())
    # Acceso protegido: obtener usuario
    resp = client.get(f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email
    # Acceso protegido: listar permisos (vacío)
    resp = client.get("/api/v1/permissions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    # Acceso con token inválido
    resp = client.get("/api/v1/users", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token inválido"

def test_register_duplicate():
    client = TestClient(app)
    user_id = str(uuid.uuid4())
    email = "dup@example.com"
    password = "dup123"
    user = {
        "id": user_id,
        "email": email,
        "full_name": "Dup User",
        "is_active": True,
        "organization_id": None,
        "roles": []
    }
    client.post("/api/v1/auth/register", params={"password": password}, json=user)
    resp = client.post("/api/v1/auth/register", params={"password": password}, json=user)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El usuario ya existe"

def test_create_and_list_org():
    client = TestClient(app)
    # Registrar y loguear usuario
    user_id = str(uuid.uuid4())
    email = "orguser@example.com"
    password = "orgpass"
    user = {
        "id": user_id,
        "email": email,
        "full_name": "Org User",
        "is_active": True,
        "organization_id": None,
        "roles": []
    }
    client.post("/api/v1/auth/register", params={"password": password}, json=user)
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    org_id = str(uuid.uuid4())
    org = {"id": org_id, "name": "OrgTest", "is_active": True}
    resp = client.post("/api/v1/organizations", json=org, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    resp = client.get("/api/v1/organizations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(o["id"] == org_id for o in resp.json())

def test_create_and_list_permission():
    client = TestClient(app)
    # Registrar y loguear usuario
    user_id = str(uuid.uuid4())
    email = "permuser@example.com"
    password = "permpass"
    user = {
        "id": user_id,
        "email": email,
        "full_name": "Perm User",
        "is_active": True,
        "organization_id": None,
        "roles": []
    }
    client.post("/api/v1/auth/register", params={"password": password}, json=user)
    resp = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    token = resp.json()["access_token"]
    perm_id = str(uuid.uuid4())
    perm = {"id": perm_id, "name": "perm_test", "description": "desc"}
    resp = client.post("/api/v1/permissions", json=perm, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    resp = client.get("/api/v1/permissions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(p["id"] == perm_id for p in resp.json())

def test_create_duplicate_user():
    client = TestClient(app)
    user = {
        "id": str(uuid.uuid4()),
        "email": "dup@example.com",
        "full_name": "Dup User",
        "is_active": True,
        "organization_id": None,
        "roles": []
    }
    client.post("/api/v1/users", json=user)
    resp = client.post("/api/v1/users", json=user)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El usuario ya existe"

def test_create_and_list_org():
    client = TestClient(app)
    org_id = str(uuid.uuid4())
    org = {"id": org_id, "name": "OrgTest", "is_active": True}
    resp = client.post("/api/v1/organizations", json=org)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    resp = client.get("/api/v1/organizations")
    assert resp.status_code == 200
    assert any(o["id"] == org_id for o in resp.json())

def test_create_and_list_permission():
    client = TestClient(app)
    perm_id = str(uuid.uuid4())
    perm = {"id": perm_id, "name": "perm_test", "description": "desc"}
    resp = client.post("/api/v1/permissions", json=perm)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    resp = client.get("/api/v1/permissions")
    assert resp.status_code == 200
    assert any(p["id"] == perm_id for p in resp.json())
