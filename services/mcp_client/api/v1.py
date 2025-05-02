from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from services.mcp_client.core.base_client import BaseClient
from shared.models import APIResponse, User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

from services.mcp_client.providers.anthropic.client import AnthropicMCPClient
from fastapi import Query
from pydantic import BaseModel

# Simulación de usuarios (en producción, consumir de User Management Service)
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Aquí se debería consultar el User Management Service vía API o shared session
    # Simulación: usuario dummy
    if token == "testtoken":
        return User(id="1", email="demo@demo.com", full_name="Demo", is_active=True, organization_id=None, roles=["admin"])
    raise HTTPException(status_code=401, detail="Token inválido")

class MessageRequest(BaseModel):
    prompt: str
    model: str = "claude-v1"

@router.get("/status", tags=["health"])
def health_check():
    """Endpoint de salud para el microservicio MCP Client."""
    return {"status": "ok"}

@router.get("/models", tags=["models"])
def list_models(current_user: User = Depends(get_current_user)):
    """
    Lista los modelos MCP disponibles (requiere autenticación JWT).
    """
    return {"models": ["claude-v1", "claude-instant-v1"]}

@router.post("/anthropic/send", tags=["anthropic"])
def send_message_anthropic(request: MessageRequest, current_user: User = Depends(get_current_user)):
    """
    Simula el envío de un mensaje a Anthropic MCP y retorna respuesta dummy tipada. (requiere autenticación JWT)
    """
    # Para entorno real, inicializar con API Key real y await send_message
    # client = AnthropicMCPClient(api_key="...")
    # resp = await client.send_message(...)
    return {
        "model": request.model,
        "prompt": request.prompt,
        "response": "Simulación de respuesta Claude (Anthropic)"
    }
