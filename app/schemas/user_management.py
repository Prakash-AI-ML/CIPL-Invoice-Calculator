from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime



# Input Schemas
class MenuPermissionInput(BaseModel):
    menu_id: int
    status: int = 1
    created_by: int

class ButtonPermissionInput(BaseModel):
    menu_id: int
    button_id: int
    button_permission: str  # e.g., "view", "add", "edit", "delete"
    status: int = 1
    created_by: int

class SubscriberInput(BaseModel):
    username: str
    email: str
    role_id: int
    status: int
    group_id: int | None = None
    password: str | None = None  # Required on create, optional on update
    company: str | None = None
    mobile: int | None = None
    created_by: int
    updated_by: int

class UserManageRequest(BaseModel):
    subscriber: SubscriberInput
    menu_permission: List[MenuPermissionInput] = []
    button_permission: List[ButtonPermissionInput] = []
    update: Literal[False, True] = False
    subscriber_id: int | None = None  # Required if update=True


# Response Schema
class PermissionDetail(BaseModel):
    id: int
    menu_id: int
    menu_name: str
    status: int

class ButtonPermissionDetail(BaseModel):
    id: int
    menu_id: int
    button_id: int
    button_name: str
    button_permission: str
    status: int

class UserManageResponse(BaseModel):
    subscriber_id: int
    username: str
    company: Optional[str] = None
    mobile: Optional[int] = None
    email: str
    role_id: int
    group_id: Optional[int] = None
    status: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    profile: Optional[str] = None
    logo: Optional[str] = None
    role_name: Optional[str] = None
    menu_permissions: List[PermissionDetail] = []
    button_permissions: List[ButtonPermissionDetail] = []

    class Config:
        from_attributes = True
