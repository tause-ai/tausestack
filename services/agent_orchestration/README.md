# Agent Orchestration Service

Servicio encargado de la orquestación de workflows de agentes y la coordinación de tareas entre microservicios.

## Estructura
- `api/`: Endpoints RESTful de este microservicio.
- `core/`: Lógica central y contratos.
- `tests/`: Pruebas unitarias y de integración.

## Convenciones
- FastAPI, Python 3.11+, tipado estricto.
- Un endpoint por archivo en `api/`.
- Documentación Google docstring.

## Seguridad y autenticación JWT
- Todos los endpoints sensibles requieren token JWT válido.
- Para pruebas locales, el token dummy aceptado es `testtoken`.
- En producción, el usuario debe autenticarse en el User Management Service y usar el token JWT real.

## Ejemplo de consumo

### 1. Verificar salud del servicio
```bash
curl http://localhost:8000/api/v1/status
```

### 2. Ejecutar un workflow multi-agente (secuencial, condicional y paralelo)

#### Campos avanzados
- `condition`: expresión booleana sobre el historial de pasos previos. Si no se cumple, el paso se omite.
- `parallel_group`: identificador para ejecutar varios pasos en paralelo.

#### Formato del request
```json
{
  "workflow": "demo_condicional_paralelo",
  "steps": [
    {"agent": "a1", "prompt": "¿Eres mayor de edad?", "model": "claude-v1"},
    {"agent": "a2", "prompt": "¿Cuál es tu país?", "model": "claude-v1", "parallel_group": "geo"},
    {"agent": "a3", "prompt": "¿Cuál es tu ocupación?", "model": "claude-v1", "parallel_group": "geo"},
    {"agent": "a4", "prompt": "Solo si país es Colombia", "condition": "steps[1]['output']['response'] == 'Colombia'"}
  ]
}
```

#### Ejemplo de llamada
```bash
curl -X POST http://localhost:8000/api/v1/workflows/execute \
    -H "Authorization: Bearer testtoken" \
    -H "Content-Type: application/json" \
    -d '{
      "workflow": "demo_condicional_paralelo",
      "steps": [
        {"agent": "a1", "prompt": "¿Eres mayor de edad?", "model": "claude-v1"},
        {"agent": "a2", "prompt": "¿Cuál es tu país?", "model": "claude-v1", "parallel_group": "geo"},
        {"agent": "a3", "prompt": "¿Cuál es tu ocupación?", "model": "claude-v1", "parallel_group": "geo"},
        {"agent": "a4", "prompt": "Solo si país es Colombia", "condition": "steps[1]['output']['response'] == 'Colombia'"}
      ]
    }'
```

#### Ejemplo de respuesta
```json
{
  "success": true,
  "message": "Workflow 'demo_condicional_paralelo' ejecutado con 4 pasos (secuenciales/paralelos)",
  "data": {
    "steps": [
      {
        "step": 1,
        "agent": "a1",
        "input": {"prompt": "¿Eres mayor de edad?", "model": "claude-v1"},
        "output": {"model": "claude-v1", "prompt": "¿Eres mayor de edad?", "response": "Simulación de respuesta Claude (Anthropic)"}
      },
      {
        "step": 2,
        "agent": "a2",
        "input": {"prompt": "¿Cuál es tu país?", "model": "claude-v1"},
        "output": {"model": "claude-v1", "prompt": "¿Cuál es tu país?", "response": "Simulación de respuesta Claude (Anthropic)"}
      },
      {
        "step": 3,
        "agent": "a3",
        "input": {"prompt": "¿Cuál es tu ocupación?", "model": "claude-v1"},
        "output": {"model": "claude-v1", "prompt": "¿Cuál es tu ocupación?", "response": "Simulación de respuesta Claude (Anthropic)"}
      },
      {
        "step": 4,
        "agent": "a4",
        "input": {"prompt": "Solo si país es Colombia", "model": "claude-v1"},
        "skipped": true,
        "reason": "Condición no satisfecha: steps[1]['output']['response'] == 'Colombia'"
      }
    ]
  }
}
```

## Flujo de orquestación multi-agente
- El endpoint `/workflows/execute` acepta una lista de pasos (`steps`), cada uno con su propio agente, prompt y modelo.
- Cada paso se ejecuta secuencialmente, llamando internamente al MCP Client Service.
- El historial de ejecución de todos los pasos y sus resultados se retorna en la respuesta.
- Todo el flujo está protegido por autenticación JWT.

## Flujo de orquestación multi-agente
- El endpoint `/workflows/execute` recibe el workflow y los datos de entrada.
- El servicio de orquestación llama internamente al MCP Client Service (`/api/v1/anthropic/send`) usando los datos recibidos.
- La respuesta del MCP Client se incluye en la respuesta final del workflow, junto con los datos de entrada originales.
- Todo el flujo está protegido por autenticación JWT.

## Tests
```bash
pytest tests/
```

---

Cada microservicio es independiente y puede escalar o desplegarse por separado. Integra autenticación y contratos compartidos para máxima seguridad y mantenibilidad.
