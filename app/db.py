from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_engine = None


def get_engine():
    """Return a cached engine instance."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def init_db() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(bind=get_engine())


def get_session() -> Session:
    engine = get_engine()
    with Session(engine) as session:
        yield session


def override_engine(engine) -> None:
    """Override engine (useful for testing)."""
    global _engine
    _engine = engine
