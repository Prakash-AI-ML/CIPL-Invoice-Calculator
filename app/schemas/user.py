from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime
from ..models.user import UserRole

# class UserBase(BaseModel):
#     username: str
#     email: EmailStr
#     role_id: int
#     group_id: Optional[int] = None
#     status: Optional[int] = 1

# class UserCreate(UserBase):
#     password: str

# class UserUpdate(BaseModel):
#     username: Optional[str] = None
#     email: Optional[EmailStr] = None
#     role_id: Optional[int] = None
#     group_id: Optional[int] = None
#     password: Optional[str] = None
#     status: Optional[int] = 1

# class UserInDB(BaseModel):
#     id: int
#     username: str
#     email: EmailStr
#     hashed_password: str
#     role_id: int
#     group_id: Optional[int] = None
#     status: Optional[int] = 1
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True

# class UserInDBBase(UserBase):
#     id: int
#     hashed_password: str
#     created_at: str

#     class Config:
#         from_attributes = True

# class UserInResponse(BaseModel):
#     id: int
#     full_name: str
#     username: str
#     email: EmailStr
#     role_id: int
#     group_id: Optional[int]
#     status: Optional[int]
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True

# class Token(BaseModel):
#     access_token: str
#     token_type: str = "bearer"

# class TokenData(BaseModel):
#     username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str
    role_id: int
    group_id: Optional[int] = None
    company_name: Optional[str] = None
    mobile: Optional[int] = None
   

class UserCreate(UserBase):
    password: str  # Will be hashed
    created_by: int = 1  # Default super admin
    updated_by: int = 1 

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[int] = None
    updated_by: int

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    group_id: Optional[int] = None
    password: Optional[str] = None  # ← Now optional
    status: Optional[int] = None
    company_name: Optional[str] = None
    mobile: Optional[int] = None
    updated_by: int

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    status: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class RoleRead(BaseModel):
    role_id: int
    role_name: str
    status:int

    class Config:
        from_attributes = True

class UserReadResponse(BaseModel):
    id: int
    company: Optional[str] = None
    mobile: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    group_id: Optional[int] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    profile: Optional[str] = None
    logo: Optional[str] = None
    status: int = 0
    role: RoleRead

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None