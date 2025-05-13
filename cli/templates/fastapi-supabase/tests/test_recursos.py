"""
Pruebas para los endpoints de recursos utilizando las herramientas de testing de TauseStack.
"""

import pytest
import asyncio
from uuid import UUID
from fastapi.testclient import TestClient
from typing import Dict, Any

from app.main import app
from app.models import Recurso

# Importaciones de TauseStack para testing
from services.testing.helpers.supabase_test_helpers import supabase_fixture, with_test_user
from services.testing.helpers.database_test_helpers import db_context, test_data_factory

# Configurar fixtures
supabase = supabase_fixture()
test_user = with_test_user()

# Cliente para pruebas
client = TestClient(app)

@pytest.mark.asyncio
async def test_crear_recurso(supabase, test_user):
    """Prueba la creación de un recurso."""
    # Configurar token de autenticación en el cliente
    token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Datos para el nuevo recurso
    data = {
        "titulo": "Recurso de prueba",
        "descripcion": "Descripción del recurso de prueba",
        "datos": {"clave": "valor"},
        "publico": True
    }
    
    # Hacer la solicitud
    response = client.post("/recursos/", json=data, headers=headers)
    
    # Verificar respuesta
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert result["titulo"] == data["titulo"]
    assert result["usuario_id"] == test_user["user_id"]
    
    # Verificar que se creó en base de datos
    recurso = await supabase.db_adapter.read(Recurso, result["id"])
    assert recurso is not None
    assert recurso.titulo == data["titulo"]

@pytest.mark.asyncio
async def test_listar_recursos(supabase, test_user, db_context, test_data_factory):
    """Prueba la obtención de la lista de recursos."""
    # Crear algunos recursos para el usuario
    await test_data_factory.create_recurso(
        usuario_id=test_user["user_id"],
        titulo="Primer recurso",
        publico=True
    )
    await test_data_factory.create_recurso(
        usuario_id=test_user["user_id"],
        titulo="Segundo recurso",
        publico=False
    )
    
    # Crear un recurso para otro usuario (pero público)
    otro_usuario_id = str(UUID.uuid4())
    await test_data_factory.create_recurso(
        usuario_id=otro_usuario_id,
        titulo="Recurso público de otro usuario",
        publico=True
    )
    
    # Hacer la solicitud
    token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/recursos/", headers=headers)
    
    # Verificar respuesta
    assert response.status_code == 200
    recursos = response.json()
    assert len(recursos) >= 3  # Al menos los 3 que creamos
    
    # Verificar que podemos ver los recursos públicos de otros usuarios
    titulos = [r["titulo"] for r in recursos]
    assert "Recurso público de otro usuario" in titulos

@pytest.mark.asyncio
async def test_actualizar_recurso(supabase, test_user):
    """Prueba la actualización de un recurso."""
    # Crear un recurso para actualizar
    data = {
        "titulo": "Recurso a actualizar",
        "descripcion": "Descripción original",
        "datos": {},
        "publico": False,
        "usuario_id": test_user["user_id"]
    }
    recurso = await supabase.create_test_data(Recurso, data)
    
    # Datos para actualizar
    update_data = {
        "titulo": "Título actualizado",
        "publico": True
    }
    
    # Hacer la solicitud
    token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.put(f"/recursos/{recurso.id}", json=update_data, headers=headers)
    
    # Verificar respuesta
    assert response.status_code == 200
    result = response.json()
    assert result["titulo"] == update_data["titulo"]
    assert result["publico"] == update_data["publico"]
    assert result["descripcion"] == data["descripcion"]  # Mantiene valor original

@pytest.mark.asyncio
async def test_eliminar_recurso(supabase, test_user):
    """Prueba la eliminación de un recurso."""
    # Crear un recurso para eliminar
    data = {
        "titulo": "Recurso a eliminar",
        "descripcion": "Este recurso será eliminado",
        "datos": {},
        "publico": False,
        "usuario_id": test_user["user_id"]
    }
    recurso = await supabase.create_test_data(Recurso, data)
    
    # Hacer la solicitud
    token = test_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete(f"/recursos/{recurso.id}", headers=headers)
    
    # Verificar respuesta
    assert response.status_code == 204
    
    # Verificar que ya no existe en la base de datos
    eliminado = await supabase.db_adapter.read(Recurso, recurso.id)
    assert eliminado is None
