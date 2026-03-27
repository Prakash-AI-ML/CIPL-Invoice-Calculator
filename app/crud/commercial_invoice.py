# app/crud/commercial_invoice.py
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial_invoice import CommercialInvoice, StatusEnum
from app.schemas.commercial_invoice import (
    CommercialInvoiceCreate,
    CommercialInvoiceUpdate,
    CommercialInvoiceOut,
)


async def create_commercial_invoice1(
    db: AsyncSession,
    data: CommercialInvoiceCreate,
    created_by: int
) -> Dict[str, Any]:

    # Optional: check if reference already exists
    existing = await db.execute(
        select(CommercialInvoice).where(
            CommercialInvoice.reference_number == data.reference_number
        )
    )
    if existing.scalars().first():
        raise ValueError(f"Reference number {data.reference_number} already exists")

    create_data = data.model_dump(exclude_none=True)
    create_data["created_by"] = created_by
    create_data["updated_by"] = created_by
    # rename key to match model column name
    create_data["raw_json"] = create_data.pop("jsondata")

    db_obj = CommercialInvoice(**create_data)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    # Return as dict (Pydantic model)
    return CommercialInvoiceOut.model_validate(db_obj).model_dump()

async def create_commercial_invoice(
    db: AsyncSession,
    data: CommercialInvoiceCreate,
    created_by: int
) -> Dict[str, Any]:

    result = await db.execute(
        select(CommercialInvoice).where(
            CommercialInvoice.reference_number == data.reference_number
        )
    )
    db_obj = result.scalars().first()

    update_data = data.model_dump(exclude_none=True)
    update_data["updated_by"] = created_by
    update_data["raw_json"] = update_data.pop("jsondata")

    if db_obj:
        # ✅ UPDATE existing record
        for key, value in update_data.items():
            setattr(db_obj, key, value)

    else:
        # ✅ CREATE new record
        update_data["created_by"] = created_by
        db_obj = CommercialInvoice(**update_data)
        db.add(db_obj)

    await db.commit()
    await db.refresh(db_obj)

    return CommercialInvoiceOut.model_validate(db_obj).model_dump()

async def get_commercial_invoices(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    reference_number: Optional[str] = None,
    status: Optional[StatusEnum] = None,
) -> List[Dict[str, Any]]:

    stmt = select(CommercialInvoice).offset(skip).limit(limit).order_by(CommercialInvoice.updated_at.desc())

    if reference_number:
        stmt = stmt.where(CommercialInvoice.reference_number.ilike(f"%{reference_number}%"))
    if status:
        stmt = stmt.where(CommercialInvoice.status == status)

    result = await db.execute(stmt)
    objects = result.scalars().all()

    # Convert all to dicts
    return [CommercialInvoiceOut.model_validate(obj).model_dump() for obj in objects]


async def get_commercial_invoice(
    db: AsyncSession,
    invoice_id: int
) -> Optional[Dict[str, Any]]:

    result = await db.execute(
        select(CommercialInvoice).where(CommercialInvoice.id == invoice_id)
    )
    obj = result.scalars().first()

    if not obj:
        return None

    return CommercialInvoiceOut.model_validate(obj).model_dump()


async def get_commercial_invoice_by_reference(
    db: AsyncSession,
    reference_number: str
) -> Optional[Dict[str, Any]]:

    result = await db.execute(
        select(CommercialInvoice).where(CommercialInvoice.reference_number == reference_number)
    )
    obj = result.scalars().first()

    if not obj:
        return None

    return CommercialInvoiceOut.model_validate(obj).model_dump()


async def update_commercial_invoice(
    db: AsyncSession,
    reference_number: str,
    update_data: CommercialInvoiceUpdate,
    updated_by: int
) -> Optional[Dict[str, Any]]:

    obj = await get_commercial_invoice_by_reference(db, reference_number)  # already dict or None
 
    if not obj:
        return None

    # Fetch ORM object for update
    orm_obj = await db.get(CommercialInvoice, obj['id'])

    if not orm_obj:
        return None
    update_dict = update_data.model_dump(exclude_none=True, exclude_unset=True)

    if "jsondata" in update_dict:
        orm_obj.raw_json = update_dict.pop("jsondata")

    for field, value in update_dict.items():
        setattr(orm_obj, field, value)

    orm_obj.updated_by = updated_by

    await db.commit()
    await db.refresh(orm_obj)

    return CommercialInvoiceOut.model_validate(orm_obj).model_dump()


async def deactivate_commercial_invoice(
    db: AsyncSession,
    invoice_id: int,
    updated_by: int
) -> bool:

    orm_obj = await db.get(CommercialInvoice, invoice_id)
    if not orm_obj:
        return False

    orm_obj.status = StatusEnum.INACTIVE
    orm_obj.updated_by = updated_by

    await db.commit()
    return True


async def delete_commercial_invoice(
    db: AsyncSession,
    invoice_id: int
) -> bool:

    result = await db.execute(
        delete(CommercialInvoice).where(CommercialInvoice.id == invoice_id)
    )
    await db.commit()

    return result.rowcount > 0