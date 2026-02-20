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

class Menu(BaseDB):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True)
    menu_name = Column(String(100), nullable=False)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    menu_permissions = relationship("MenuPermission", back_populates="menu")
    button_permissions = relationship("ButtonPermission", back_populates="menu")
    buttons = relationship("Button", back_populates="menu")

class MenuPermission(BaseDB):
    __tablename__ = "menu_permissions"
    id = Column(Integer, primary_key=True, index=True)
    subscribers_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)  # User-specific
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="menu_permissions")
    menu = relationship("Menu", back_populates="menu_permissions")
    
