# Interfaces MCP

Este directorio contiene las interfaces abstractas para la integración de clientes y servidores MCP (Multi-Call Protocol) en aplicaciones Tausestack.

## Interfaces Principales

### MCPClient

La interfaz `MCPClient` define el contrato que deben implementar todos los adaptadores de cliente MCP, independientemente del proveedor específico (Anthropic, OpenAI, etc.).

```python
from services.mcp_client.interfaces.mcp_client import MCPClient

class MiClienteMCP(MCPClient):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `initialize`: Inicializa el cliente con configuración
- `list_tools`: Obtiene las herramientas disponibles
- `call_tool`: Llama a una herramienta específica
- `get_manifest`: Obtiene el manifiesto del servidor
- `send_message`: Envía un mensaje al proveedor
- `send_batch`: Procesa un lote de mensajes

### MCPServer

La interfaz `MCPServer` define el contrato para implementar servidores que exponen herramientas como un proveedor MCP.

```python
from services.mcp_client.interfaces.mcp_server import MCPServer

class MiServidorMCP(MCPServer):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `register_tool`: Registra una nueva herramienta
- `unregister_tool`: Elimina una herramienta
- `handle_call`: Procesa llamadas a herramientas
- `get_tools`: Lista las herramientas disponibles
- `generate_manifest`: Genera el manifiesto completo

### MCPMessage

Modelos de datos estandarizados para la comunicación MCP:

```python
from services.mcp_client.interfaces.mcp_message import MCPMessage, MCPBatchRequest

# Crear un mensaje
mensaje = MCPMessage(
    role="user",
    content="Hola, necesito ayuda con..."
)

# Crear una solicitud por lotes
batch = MCPBatchRequest(
    messages=[mensaje],
    model="claude-3-sonnet"
)
```

## Recomendaciones de Implementación

1. Extiende estas interfaces para crear adaptadores concretos
2. Utiliza tipos estrictos en tus implementaciones
3. Maneja correctamente las excepciones del proveedor
4. Considera la asincronía en todas las operaciones de red
