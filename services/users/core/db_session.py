from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os

DB_URL = os.getenv("TAUSESTACK_DB_URL", "postgresql+psycopg2://tausestack:tausestack@localhost:5432/tausestack")
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
