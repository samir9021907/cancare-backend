"""
Database Connection and Session Management.

Sets up SQLAlchemy for SQLite and yields database sessions for API requests.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from app.config import settings

# SQLite requires `check_same_thread: False` to allow multi-threaded requests in FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True if you want to see all raw SQL queries printed
)

# Factory for creating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session to endpoints.
    Automatically closes the session when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

