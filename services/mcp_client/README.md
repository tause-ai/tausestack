# MCP Client Service

Servicio encargado de la comunicación con proveedores MCP (Anthropic, Google, etc.) y la lógica central para modelos, mensajes y herramientas.

## Estructura
- `api/`: Endpoints RESTful de este microservicio.
- `core/`: Lógica central y contratos.
- `providers/`: Integraciones con proveedores externos.
- `adapters/`: Adaptadores de dominio (ej: marketing, SEO).
- `tests/`: Pruebas unitarias y de integración.

## Convenciones
- FastAPI, Python 3.11+, tipado estricto.
- Un endpoint por archivo en `api/`.
- Documentación Google docstring.

## Seguridad y autenticación JWT
- Todos los endpoints sensibles requieren token JWT válido.
- En producción, el usuario debe autenticarse en el User Management Service, obtener un token y usarlo en las peticiones.
- Para pruebas locales, el token dummy aceptado es `testtoken`.

## Ejemplo de consumo

### 1. Obtener modelos disponibles (requiere JWT)
```bash
curl -H "Authorization: Bearer testtoken" http://localhost:8000/api/v1/models
```

### 2. Enviar mensaje a Anthropic (requiere JWT)
```bash
curl -X POST http://localhost:8000/api/v1/anthropic/send \
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
