# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
from ..db.base_class import BaseDB



class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

class Role(BaseDB):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)  # Assuming user_id
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")
 