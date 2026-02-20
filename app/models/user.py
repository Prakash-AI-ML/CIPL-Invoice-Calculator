

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


from enum import Enum as PyEnum

class UserRole(PyEnum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"
    accountant = "accountant"



from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import BaseDB
# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

class User(BaseDB):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=False, index=False, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    group_id = Column(Integer, nullable=True)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, nullable=False)  # Assuming user_id
    updated_by = Column(Integer, nullable=False)
    profile_path = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    company_logo = Column(String(255), nullable=True)
    mobile = Column(BIGINT(), nullable=True)


    # Relationships
    role = relationship("Role", back_populates="users")
    menu_permissions = relationship("MenuPermission", back_populates="user")
    button_permissions = relationship("ButtonPermission", back_populates="user")
