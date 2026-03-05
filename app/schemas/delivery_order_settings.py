from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

# Pydantic Schemas
class DeliveryOrderBase(BaseModel):
    company_name: str
    address: str
    company_logo: str
    status: int = StatusEnum.ACTIVE.value

class DeliveryOrderCreate(DeliveryOrderBase):
    created_by: int
    updated_by: int

class DeliveryOrderUpdate(BaseModel):
    company_name: Optional[str] = None
    address: Optional[str] = None
    company_logo: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class DeliveryOrderResponse(DeliveryOrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True
