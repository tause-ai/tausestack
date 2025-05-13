from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from .db import SessionLocal
from .db_models import Workflow, WorkflowExecution
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import update, delete
from datetime import datetime

class ExecutionHistory:
    @staticmethod
    def list_executions() -> List[Dict[str, Any]]:
        session: Session = SessionLocal()
        try:
            executions = session.execute(select(WorkflowExecution)).scalars().all()
            return [
                {
                    "id": str(e.id),
                    "workflow": session.get(Workflow, e.workflow_id).name if e.workflow_id else None,
                    "input_data": e.input_data,
                    "steps": e.steps,
                    "history": e.history,
                    "error": e.error,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "finished_at": e.finished_at.isoformat() if e.finished_at else None
                }
                for e in executions
            ]
        finally:
            session.close()

    @staticmethod
    def save_execution(execution: Dict[str, Any]):
        session: Session = SessionLocal()
        try:
            # Buscar workflow_id por nombre
            workflow_name = execution.get("workflow")
            workflow_obj = session.execute(select(Workflow).where(Workflow.name == workflow_name)).scalar_one_or_none()
            workflow_id = workflow_obj.id if workflow_obj else None
            e = WorkflowExecution(
                workflow_id=workflow_id,
                input_data=execution.get("input_data"),
                steps=execution.get("steps"),
                history=execution.get("history"),
                error=execution.get("error"),
                started_at=datetime.fromisoformat(execution["started_at"]) if execution.get("started_at") else datetime.utcnow(),
                finished_at=datetime.fromisoformat(execution["finished_at"]) if execution.get("finished_at") else datetime.utcnow()
            )
            session.add(e)
            session.commit()
        except SQLAlchemyError as ex:
            session.rollback()
            raise ex
        finally:
            session.close()

    @staticmethod
    def get_execution(exec_id: str) -> Dict[str, Any]:
        session: Session = SessionLocal()
        try:
            e = session.get(WorkflowExecution, exec_id)
            if not e:
                return {}
            workflow = session.get(Workflow, e.workflow_id)
            return {
                "id": str(e.id),
                "workflow": workflow.name if workflow else None,
                "input_data": e.input_data,
                "steps": e.steps,
                "history": e.history,
                "error": e.error,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "finished_at": e.finished_at.isoformat() if e.finished_at else None
            }
        finally:
            session.close()
