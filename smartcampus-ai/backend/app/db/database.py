"""
SmartCampus AI — Database Setup (SQLAlchemy + SQLite)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# For SQLite, need check_same_thread=False for FastAPI's async usage
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """FastAPI dependency — yields a database session, auto-closes on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined by models inheriting from Base."""
    import app.models  # noqa: F401 — register all models with Base
    Base.metadata.create_all(bind=engine)
