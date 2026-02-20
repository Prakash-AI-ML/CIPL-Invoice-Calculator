# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..db.base_class import BaseDB

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0


class Button(BaseDB):
    __tablename__ = "buttons"
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    button_name = Column(String(100), nullable=False)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    menu = relationship("Menu", back_populates="buttons")

class ButtonPermission(BaseDB):
    __tablename__ = "button_permissions"
    id = Column(Integer, primary_key=True, index=True)
    subscribers_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)  # User-specific
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    button_id = Column(Integer, ForeignKey("buttons.id"), nullable=False)
    button_permission = Column(String(50), nullable=False)  # e.g., 'view', 'edit', 'delete', 'add'
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="button_permissions")
    menu = relationship("Menu", back_populates="button_permissions")
    button = relationship("Button")