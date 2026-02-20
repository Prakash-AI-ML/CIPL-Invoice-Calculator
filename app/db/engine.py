from sqlalchemy import create_engine
# from .config import settings  # Wait, config is in core, import from there.

from app.core.config import settings

engine = create_engine(settings.database_url)