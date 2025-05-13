from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from shared.models import User, APIResponse
from services.users.core.auth import verify_password, get_password_hash, create_access_token, decode_access_token
from sqlalchemy.orm import Session
from services.users.core.db_session import get_db
import uuid

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

@router.post("/register", response_model=APIResponse, tags=["auth"])
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    from shared.models import User  # Importación local para evitar conflictos circulares
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    hashed = get_password_hash(user_in.password)
    user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        full_name=user_in.full_name,
        is_active=True,
        organization_id=None,
        roles=[]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Guardar el hash en un campo password_hash si existe, o crear uno en el modelo real
    db.execute(f"UPDATE users SET password_hash = '{hashed}' WHERE id = '{user.id}'")
    db.commit()
    return APIResponse(success=True, message="Usuario registrado", data=user.dict())

@router.post("/token", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    # Obtener el hash desde la base de datos
    result = db.execute(f"SELECT password_hash FROM users WHERE id = '{user.id}'").fetchone()
    password_hash = result[0] if result else ""
    if not verify_password(form_data.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User, tags=["auth"])
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
