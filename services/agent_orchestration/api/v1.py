from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from shared.models import APIResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Simulación: en producción, validar contra User Management Service
    if token == "testtoken":
        return {"id": "1", "email": "demo@demo.com"}
    raise HTTPException(status_code=401, detail="Token inválido")

from typing import Dict, Any

from typing import Optional
class WorkflowStep(BaseModel):
    agent: str
    prompt: str
    model: str = "claude-v1"
    condition: Optional[str] = None  # Expresión booleana sobre el historial, ej: "steps[0]['output']['response'] == 'ok'"
    parallel_group: Optional[str] = None  # Identificador para ejecución paralela

class OrchestrationRequest(BaseModel):
    workflow: str
    steps: List[WorkflowStep]
    input_data: Optional[Dict[str, Any]] = None

@router.get("/status", tags=["health"])
def health_check():
    """Endpoint de salud para el microservicio de orquestación."""
    return {"status": "ok"}

import httpx

import threading

@router.post("/workflows/execute", response_model=APIResponse, tags=["workflows"])
def execute_workflow(request: OrchestrationRequest, current_user=Depends(get_current_user)):
    """
    Ejecuta un workflow multi-agente avanzado y registra la ejecución en el historial.
    - Permite ejecución secuencial, condicional y paralela de pasos.
    - Cada paso puede tener un campo 'condition' (expresión booleana sobre el historial) y 'parallel_group' (identificador de grupo paralelo).
    - Se retorna el historial completo de ejecución.
    - Protegido por JWT.
    """
    history = []
    step_results = []
    exec_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()
    try:
        with httpx.Client() as client:
            # Agrupar pasos por parallel_group (None = secuencial)
            steps_grouped = {}
            for idx, step in enumerate(request.steps):
                group = step.parallel_group or f"__seq__{idx}"
                if group not in steps_grouped:
                    steps_grouped[group] = []
                steps_grouped[group].append((idx, step))
            # Ejecutar grupos
            for group, steps_in_group in steps_grouped.items():
                threads = []
                group_results = [None] * len(steps_in_group)
                def run_step(idx_in_group, idx, step):
                    # Evaluar condición si existe
                    if step.condition:
                        try:
                            cond = eval(step.condition, {"steps": history})
                        except Exception:
                            cond = False
                        if not cond:
                            group_results[idx_in_group] = {
                                "step": idx + 1,
                                "agent": step.agent,
                                "input": {"prompt": step.prompt, "model": step.model},
                                "skipped": True,
                                "reason": f"Condición no satisfecha: {step.condition}"
                            }
                            return
                    payload = {"prompt": step.prompt, "model": step.model}
                    resp = client.post(
                        "http://localhost:8000/api/v1/anthropic/send",
                        headers={"Authorization": "Bearer testtoken"},
                        json=payload
                    )
                    result = resp.json() if resp.status_code == 200 else {"error": resp.text}
                    group_results[idx_in_group] = {
                        "step": idx + 1,
                        "agent": step.agent,
                        "input": payload,
                        "output": result
                    }
                # Ejecutar en paralelo si hay más de un paso en el grupo
                for idx_in_group, (idx, step) in enumerate(steps_in_group):
                    t = threading.Thread(target=run_step, args=(idx_in_group, idx, step))
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()
                # Añadir resultados al historial en orden
                for res in group_results:
                    if res: history.append(res)
    except Exception as e:
        # Registrar error en historial
        ExecutionHistory.save_execution({
            "id": exec_id,
            "workflow": request.workflow,
            "input_data": request.input_data,
            "steps": [s.dict() for s in request.steps],
            "history": history,
            "error": str(e),
            "started_at": started_at,
            "finished_at": datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"Error llamando a MCP Client: {str(e)}")
    # Guardar ejecución exitosa
    ExecutionHistory.save_execution({
        "id": exec_id,
        "workflow": request.workflow,
        "input_data": request.input_data,
        "steps": [s.dict() for s in request.steps],
        "history": history,
        "started_at": started_at,
        "finished_at": datetime.utcnow().isoformat()
    })
    return APIResponse(
        success=True,
        message=f"Workflow '{request.workflow}' ejecutado con {len(history)} pasos (secuenciales/paralelos)",
        data={
            "steps": history,
            "input_data": request.input_data,
            "execution_id": exec_id
        }
    )
