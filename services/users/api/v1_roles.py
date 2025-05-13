from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from shared.models import Role, APIResponse, User
from services.users.core.db_session import get_db
from services.users.core.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.post("/roles", response_model=APIResponse, tags=["roles"])
def create_role(role: Role, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Role).filter(Role.name == role.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="El rol ya existe")
    db.add(role)
    db.commit()
    db.refresh(role)
    return APIResponse(success=True, message="Rol creado", data=role.dict())

@router.get("/roles", response_model=list[Role], tags=["roles"])
def list_roles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Role).all()

@router.post("/roles/{role_id}/assign/{user_id}", response_model=APIResponse, tags=["roles"])
def assign_role(role_id: str, user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user or not role:
        raise HTTPException(status_code=404, detail="Usuario o rol no encontrado")
    if role in user.roles:
        raise HTTPException(status_code=400, detail="El usuario ya tiene este rol")
    user.roles.append(role)
    db.commit()
    return APIResponse(success=True, message="Rol asignado", data={"user_id": user.id, "role_id": role.id})

@router.delete("/roles/{role_id}", response_model=APIResponse, tags=["roles"])
def delete_role(role_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    db.delete(role)
    db.commit()
    return APIResponse(success=True, message="Rol eliminado", data={"role_id": role_id})

@router.post("/roles/{role_id}/remove/{user_id}", response_model=APIResponse, tags=["roles"])
def remove_role_from_user(role_id: str, user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user or not role:
        raise HTTPException(status_code=404, detail="Usuario o rol no encontrado")
    if role not in user.roles:
        raise HTTPException(status_code=400, detail="El usuario no tiene este rol")
    user.roles.remove(role)
    db.commit()
    return APIResponse(success=True, message="Rol removido del usuario", data={"user_id": user.id, "role_id": role.id})

@router.get("/roles/{role_id}/users", response_model=list[User], tags=["roles"])
def list_users_by_role(role_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return role.users
