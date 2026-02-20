from typing import Any, Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

Base = declarative_base(cls=AsyncAttrs)  # For async attr access

class BaseDB(Base):
    __abstract__ = True

    id: Any
    full_name: str
    username: str
    email: str
    hashed_password: str
    role: str
    group_id: Optional[int] = None