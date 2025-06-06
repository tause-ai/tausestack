import pytest
import pytest_asyncio
import os
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

@pytest_asyncio.fixture(scope="class")
async def adapter():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        pytest.skip("No hay configuración de Supabase para pruebas.")
    adapter = SupabaseDatabaseAdapter()
    ok = await adapter.initialize({"supabase_url": url, "supabase_key": key})
    assert ok
    yield adapter
    await adapter.close()

@pytest.mark.asyncio
class TestSupabaseDatabaseAdapter:

    @pytest.mark.asyncio
    async def test_crud_user(self, adapter):
        # Crear
        user = await adapter.create(User, {"name": "Test User", "email": "testuser@tause.ai"})
        assert user.name == "Test User"
        assert user.email == "testuser@tause.ai"
        # Leer
        user2 = await adapter.read(User, user.id)
        assert user2 and user2.id == user.id
        # Actualizar
        updated = await adapter.update(User, user.id, {"name": "Usuario Modificado"})
        assert updated.name == "Usuario Modificado"
        # Query
        res = await adapter.query(User, conditions=None)
        assert any(u.id == user.id for u in res.data)
        # Eliminar
        ok = await adapter.delete(User, user.id)
        assert ok
        user3 = await adapter.read(User, user.id)
        assert user3 is None

    @pytest.mark.asyncio
    async def test_query_advanced(self, adapter):
        # Crear varios usuarios
        users = [
            await adapter.create(User, {"name": f"User{i}", "email": f"user{i}@tause.ai"})
            for i in range(3)
        ]
        # Query con filtro
        from services.database.interfaces.db_adapter import FilterCondition
        cond = [FilterCondition(field="name", op="eq", value="User1")]
        res = await adapter.query(User, conditions=cond)
        assert len(res.data) == 1 and res.data[0].name == "User1"
        # Query con ordenamiento y límite
        from services.database.interfaces.db_adapter import QueryOptions
        opts = QueryOptions(order_by=["-id"], limit=2)
        res = await adapter.query(User, options=opts)
        assert len(res.data) == 2
        # Limpieza
        for u in users:
            await adapter.delete(User, u.id)

    @pytest.mark.asyncio
    async def test_transaction(self, adapter):
        # Simular una transacción (si el adaptador lo soporta)
        try:
            async with adapter.transaction():
                u1 = await adapter.create(User, {"name": "TxUser1", "email": "tx1@tause.ai"})
                u2 = await adapter.create(User, {"name": "TxUser2", "email": "tx2@tause.ai"})
                raise Exception("Rollback!")
        except Exception:
            pass
        # Verificar que ninguno fue persistido
        users = await adapter.query(User, conditions=[{"field": "email", "op": "like", "value": "%tx%@tause.ai"}])
        assert not users.data

    @pytest.mark.asyncio
    async def test_error_handling(self, adapter):
        # Intentar leer un usuario inexistente
        user = await adapter.read(User, 999999)
        assert user is None
        # Intentar crear usuario con datos inválidos
        with pytest.raises(Exception):
            await adapter.create(User, {"name": None, "email": "bad@tause.ai"})
