from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

# Pydantic Schemas
class RoleBase(BaseModel):
    role_name: str
    status: int = StatusEnum.ACTIVE.value

class RoleCreate(RoleBase):
    created_by: int
    updated_by: int

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True
