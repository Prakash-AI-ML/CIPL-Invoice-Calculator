from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

class StatusEnum(PyEnum):
    ACTIVE = 1
    INACTIVE = 0


class ButtonBase(BaseModel):
    button_name: str
    menu_id: int
    status: int = StatusEnum.ACTIVE.value

class ButtonCreate(ButtonBase):
    created_by: int

class ButtonUpdate(BaseModel):
    button_name: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class ButtonResponse(ButtonBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int

    class Config:
        from_attributes = True


class ButtonPermissionBase(BaseModel):
    subscribers_id: int
    menu_id: int
    button_id: int
    button_permission: str
    status: int = StatusEnum.ACTIVE.value

class ButtonPermissionCreate(ButtonPermissionBase):
    created_by: int


class ButtonPermissionUpdate(BaseModel):
    button_permission: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class ButtonPermissionUpdate1(BaseModel):
    button_permission: Optional[str] = None
    status: Optional[int] = None
    updated_by: int

class ButtonPermissionResponse(ButtonPermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: int
    class Config:
        from_attributes = True