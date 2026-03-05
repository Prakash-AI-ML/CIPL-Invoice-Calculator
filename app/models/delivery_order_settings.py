

from ..db.base_class import BaseDB

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BIGINT
from sqlalchemy.sql import func
from enum import Enum as PyEnum

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

class DeliveryOrder(BaseDB):
    __tablename__ = "delivery_order_settings"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=False)
    company_logo = Column(String(255), nullable=True)
    status = Column(Integer, default=StatusEnum.ACTIVE.value, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
