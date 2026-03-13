from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CiplDescBase(BaseModel):
    item_id: Optional[int] = None
    original: str = Field(..., max_length=500)
    modified: str = Field(..., max_length=500)
    lines: int

class CiplDescCreate(CiplDescBase):
    pass

class CiplDescUpdate(BaseModel):
    item_id: Optional[int] = None
    original: Optional[str] = Field(None, max_length=500)
    modified: Optional[str] = Field(None, max_length=500)
    lines: Optional[int] = None
    status: Optional[int] = None

class CiplDescOut(CiplDescBase):
    id: int
    status: str
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class CiplDescList(BaseModel):
    data: List[CiplDescOut]
    total: int