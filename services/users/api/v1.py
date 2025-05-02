from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from shared.models import User, Organization, Permission, APIResponse
from pydantic import BaseModel, EmailStr
from typing import List
from services.users.api.auth import router as auth_router, users_db, user_passwords
from services.users.core.auth import decode_access_token

router = APIRouter()
router.include_router(auth_router, prefix="/auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
organizations_db: List[Organization] = []
permissions_db: List[Permission] = []

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = next((u for u in users_db if u.id == payload["sub"]), None)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# --- Endpoints de usuarios ---
@router.get("/users", response_model=List[User], tags=["usuarios"])
def list_users(current_user: User = Depends(get_current_user)):
    return users_db

@router.get("/users/{user_id}", response_model=User, tags=["usuarios"])
def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# --- Endpoints de organizaciones ---
@router.post("/organizations", response_model=APIResponse, tags=["organizaciones"])
def create_org(org: Organization, current_user: User = Depends(get_current_user)):
    if any(o.name == org.name for o in organizations_db):
        raise HTTPException(status_code=400, detail="La organización ya existe")
    organizations_db.append(org)
    return APIResponse(success=True, message="Organización creada", data=org.dict())

@router.get("/organizations", response_model=List[Organization], tags=["organizaciones"])
def list_orgs(current_user: User = Depends(get_current_user)):
    return organizations_db

# --- Endpoints de permisos ---
@router.post("/permissions", response_model=APIResponse, tags=["permisos"])
def create_permission(perm: Permission, current_user: User = Depends(get_current_user)):
    if any(p.name == perm.name for p in permissions_db):
        raise HTTPException(status_code=400, detail="El permiso ya existe")
    permissions_db.append(perm)
    return APIResponse(success=True, message="Permiso creado", data=perm.dict())

@router.get("/permissions", response_model=List[Permission], tags=["permisos"])
def list_permissions(current_user: User = Depends(get_current_user)):
    return permissions_db
