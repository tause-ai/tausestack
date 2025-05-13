from typing import List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from .db import SessionLocal
from .db_models import Workflow
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import update, delete
from datetime import datetime

class WorkflowStore:
    @staticmethod
    def list_workflows() -> List[Dict[str, Any]]:
        session: Session = SessionLocal()
        try:
            workflows = session.execute(select(Workflow)).scalars().all()
            return [
                {
                    "workflow": w.name,
                    "description": w.description,
                    "definition": w.definition,
                    "created_at": w.created_at.isoformat(),
                    "updated_at": w.updated_at.isoformat() if w.updated_at else None
                }
                for w in workflows
            ]
        finally:
            session.close()

    @staticmethod
    def save_workflow(workflow: Dict[str, Any]):
        session: Session = SessionLocal()
        try:
            existing = session.execute(select(Workflow).where(Workflow.name == workflow["workflow"])).scalar_one_or_none()
            if existing:
                existing.description = workflow.get("description")
                existing.definition = workflow.get("definition")
                existing.updated_at = datetime.utcnow()
            else:
                w = Workflow(
                    name=workflow["workflow"],
                    description=workflow.get("description"),
                    definition=workflow.get("definition"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(w)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_workflow(name: str) -> Dict[str, Any]:
        session: Session = SessionLocal()
        try:
            w = session.execute(select(Workflow).where(Workflow.name == name)).scalar_one_or_none()
            if not w:
                return {}
            return {
                "workflow": w.name,
                "description": w.description,
                "definition": w.definition,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
        finally:
            session.close()

    @staticmethod
    def delete_workflow(name: str):
        session: Session = SessionLocal()
        try:
            session.execute(delete(Workflow).where(Workflow.name == name))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
