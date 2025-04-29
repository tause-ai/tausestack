# Esquemas de request para autenticación
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
