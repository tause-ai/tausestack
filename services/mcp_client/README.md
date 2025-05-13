# MCP Client Framework

Librería base para integrar y extender clientes MCP (Multi-Call Protocol) en aplicaciones Tausestack. Esta biblioteca proporciona interfaces abstractas y utilidades para crear adaptadores personalizados para diferentes proveedores MCP (Anthropic, OpenAI, etc.).

## ¿Qué es MCP?

El Model Context Protocol (MCP) es un estándar que conecta sistemas de IA con herramientas y servicios externos, permitiendo:

- Exponer funcionalidades como "herramientas" para modelos de IA
- Consumir servicios externos a través de una interfaz estandarizada
- Orquestar flujos de trabajo con herramientas inteligentes

## Estructura del Framework

- `interfaces/`: Contratos e interfaces abstractas para implementar clientes y servidores MCP
- `core/`: Lógica central y clases base
- `adapters/`: Adaptadores de dominio (clases abstractas o utilidades comunes)
- `providers/`: Ejemplos de integraciones con proveedores específicos
- `tests/`: Pruebas unitarias y de integración

## Interfaces Principales

### MCPClient

Base para implementar clientes que consumen herramientas MCP externas:

```python
from services.mcp_client.interfaces.mcp_client import MCPClient

class MyCustomMCPClient(MCPClient):
    async def initialize(self, config):
        # Implementación personalizada
        pass
        
    async def list_tools(self):
        # Obtener herramientas disponibles
        pass
        
    async def call_tool(self, tool_name, params):
        # Llamar a una herramienta específica
        pass
```

### MCPServer

Base para exponer tus propias herramientas como servidor MCP:

```python
from services.mcp_client.interfaces.mcp_server import MCPServer

class MyCustomMCPServer(MCPServer):
    async def register_tool(self, tool_name, tool_config):
        # Registrar una nueva herramienta
        pass
```
    -H "Authorization: Bearer testtoken" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Hola Claude!", "model": "claude-v1"}'
```

### 3. Ejemplo de respuesta
```json
{
  "model": "claude-v1",
  "prompt": "Hola Claude!",
  "response": "Simulación de respuesta Claude (Anthropic)"
}
```

## Tests
```bash
pytest tests/
```

---

Cada microservicio es independiente y puede escalar o desplegarse por separado. Integra autenticación y contratos compartidos para máxima seguridad y mantenibilidad.
