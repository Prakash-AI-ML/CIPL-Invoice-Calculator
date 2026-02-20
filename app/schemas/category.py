from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0

# Pydantic Schemas
class CategoryBase(BaseModel):
    category_name: str
    status: int = StatusEnum.ACTIVE.value

class CategoryCreate(CategoryBase):
    created_by: int
    updated_by: int

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True
