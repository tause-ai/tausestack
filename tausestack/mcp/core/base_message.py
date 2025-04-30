from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class MCPMessage(BaseModel):
    """Mensaje MCP según la especificación Anthropic."""
    role: str
    content: Union[str, Dict[str, Any], List[Any]]
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_result: Optional[Any] = None
    # Puedes agregar más campos según la evolución del protocolo

class MCPBatchRequest(BaseModel):
    """Batch de mensajes MCP para procesamiento por lotes."""
    messages: List[MCPMessage]
    model: str
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # Otros campos MCP relevantes

class MCPBatchResponse(BaseModel):
    """Respuesta batch MCP."""
    results: List[Any]
    raw_response: Dict[str, Any]
