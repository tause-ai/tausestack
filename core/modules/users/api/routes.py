# Rutas de usuarios (ejemplo)
from fastapi import APIRouter

router = APIRouter()

@router.get('/')
def list_users():
    return [{"id": 1, "username": "admin"}]
