# Global FastAPI dependencies
from app.db.database import get_db


def get_current_user():
    """Placeholder for future authentication middleware.
    Returns None until auth system is implemented."""
    return None


def get_db_session():
    """Yields a SQLAlchemy database session via the canonical get_db generator."""
    return get_db()
