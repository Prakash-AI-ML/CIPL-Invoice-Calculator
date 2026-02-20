from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0


class MenuBase(BaseModel):
    menu_name: str
    status: int = StatusEnum.ACTIVE.value

class MenuCreate(MenuBase):
    created_by: int

class MenuUpdate(BaseModel):
    menu_name: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class MenuResponse(MenuBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True


class MenuPermissionBase(BaseModel):
    subscribers_id: int
    menu_id: int
    status: int = StatusEnum.ACTIVE.value

class MenuPermissionCreate(MenuPermissionBase):
    created_by: int

class MenuPermissionUpdate(BaseModel):
    menu_id: int
    status: Optional[int] = None
    updated_by: int

class MenuPermissionUpdate1(BaseModel):
    menu_id: int
    status: Optional[int] = None
    updated_by: int

class MenuPermissionResponse(MenuPermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
    class Config:
        from_attributes = True