from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DB_URL = os.getenv("TAUSESTACK_DB_URL", "postgresql+psycopg2://tausestack:tausestack@localhost:5432/tausestack")

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
