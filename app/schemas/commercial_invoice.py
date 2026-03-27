
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CommercialInvoiceCreate(BaseModel):
    reference_number: str = Field(..., max_length=80, description="Unique invoice reference (e.g. ES-00130)")
    jsondata: Dict[str, Any] = Field(..., description="Full parsed invoice JSON data")
    is_original: bool = Field(True, description="True if this is the original extracted version")
    job_number: Optional[str] = Field(None, description="e.g. TPL/00xxP/MM/YY")
    group_number: Optional[str] = Field(None, description="e.g. ES-00136,ES-00137,ES-00140,ES-00141...")
    divided_by: Optional[float] = Field(None, description="Custom division factor if applicable")


class CommercialInvoiceUpdate(BaseModel):
    jsondata: Optional[Dict[str, Any]] = Field(None)
    is_original: Optional[bool] = Field(None)
    job_number: Optional[str] = Field(None, description="e.g. TPL/00xxP/MM/YY")
    group_number: Optional[str] = Field(None, description="e.g. ES-00136,ES-00137,ES-00140,ES-00141...")
    divided_by: Optional[float] = Field(None)
    status: Optional[StatusEnum] = Field(None)


class CommercialInvoiceOut1(BaseModel):
    id: int
    reference_number: str
    jsondata: Dict[str, Any]                # returned as proper dict
    is_original: bool
    divided_by: Optional[float]
    status: StatusEnum
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  
    )
class CommercialInvoiceOut(BaseModel):
    id: int
    reference_number: str
    
    jsondata: Dict[str, Any] = Field(..., alias="raw_json")   # ← key change
    
    is_original: bool
    divided_by: Optional[float]
    job_number: Optional[str]
    group_number: Optional[str]
    status: StatusEnum
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,          # ← important: allows both alias and field name
    )