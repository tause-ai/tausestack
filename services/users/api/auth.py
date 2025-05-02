from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from shared.models import User, APIResponse
from services.users.core.auth import verify_password, get_password_hash, create_access_token, decode_access_token
from typing import List
import uuid

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

# Simulación de usuarios con contraseña hasheada
users_db: List[User] = []
user_passwords = {}  # user_id: hashed_password

@router.post("/register", response_model=APIResponse, tags=["auth"])
def register_user(user: User, password: str):
    if any(u.email == user.email for u in users_db):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    hashed = get_password_hash(password)
    users_db.append(user)
    user_passwords[user.id] = hashed
    return APIResponse(success=True, message="Usuario registrado", data=user.dict())

@router.post("/token", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = next((u for u in users_db if u.email == form_data.username), None)
    if not user or not verify_password(form_data.password, user_passwords.get(user.id, "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User, tags=["auth"])
def get_me(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = next((u for u in users_db if u.id == payload["sub"]), None)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
