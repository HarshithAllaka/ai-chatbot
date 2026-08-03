from app.db.base import Base
from app.db.database import engine

# Import all models so SQLAlchemy registers them
import app.models


def init_db() -> None:
    Base.metadata.create_all(bind=engine)