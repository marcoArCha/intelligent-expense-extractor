import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expenses.db")

# Move check_same_thread inside connect_args for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy 2.0 models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for managing DB session lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        