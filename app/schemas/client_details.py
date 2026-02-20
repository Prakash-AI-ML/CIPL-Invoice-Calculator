from pydantic import BaseModel
from typing import Optional

class ClientCreate(BaseModel):
    client_id: Optional[str] = None
    name: str
    phone: Optional[int] = None
    address: Optional[str] = None
    pay_term: int
    merchant_category: str
    template: int
    bank_name: Optional[str] = None
    bank_acc_number: Optional[int] = None
    bank_origin: Optional[str] = None
    swift_code: Optional[str] = None
    iban_no: Optional[str] = None
    status: Optional[int] = 1
    created_by: int
    updated_by: int


class ClientUpdate(ClientCreate):
    pass
