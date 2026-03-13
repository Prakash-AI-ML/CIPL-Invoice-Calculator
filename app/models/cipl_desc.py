

from ..db.base_class import BaseDB

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from sqlalchemy import Enum

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

class CiplDesc(BaseDB):
    __tablename__ = "cipl_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=True)
    original = Column(String(500), nullable=False)
    modified = Column(String(500), nullable=False)
    lines = Column(Integer, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
