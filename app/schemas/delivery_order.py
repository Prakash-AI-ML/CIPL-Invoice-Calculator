from pydantic import BaseModel, Field
from typing import Optional


class CollectionDetails(BaseModel):
    address: str
    contact_person: Optional[str] = ""
    tel: Optional[str] = ""
    date: Optional[str] = Field(None, description="Format: DD-MM-YYYY")
    time: Optional[str] = ""
    truck_type: str
    truck_number: str
    driver: str
    date_: Optional[str] = Field(None, description="Format: DD-MM-YYYY")


class DeliveryDetails(BaseModel):
    address: str
    contact_person: Optional[str] = ""
    tel: Optional[str] = ""
    date: Optional[str] = Field(None, description="Format: DD-MM-YYYY")
    time: Optional[str] = ""
    name: Optional[str] = ""
    id: Optional[str] = ""
    signature: Optional[str] = ""
    date_: Optional[str] = ""


class LogisticsDocument(BaseModel):
    serial_no: str
    ref_no: str
    po_no: str
    date: str = Field(..., description="Format: DD/MM/YYYY")

    collection_details: CollectionDetails
    delivery_details: DeliveryDetails

    total_packages: str
    total_weight: str
    cargo_description: str
    cargo_ref: str
    remarks: Optional[str] = ""

    class Config:
        extra = "forbid"