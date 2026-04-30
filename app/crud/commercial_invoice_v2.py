from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy import select, delete
from app.models.commercial_invoice_v2 import CiplList, StatusEnum
from app.schemas.commercial_invoice_v2 import CiplListCreate, CiplListUpdate
from app.models.commercial_invoice_v2 import CommercialInvoiceV2 as CommercialInvoice
from app.schemas.commercial_invoice_v2 import (
    CommercialInvoiceCreate,
    CommercialInvoiceUpdate,
    CommercialInvoiceOut,
)

# CREATE
async def create_cipl_list_db(db: AsyncSession, obj_in: CiplListCreate) -> CiplList:
    db_obj = CiplList(
        **obj_in.model_dump(),
        status=StatusEnum.ACTIVE
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj





async def create_cipl_list_db1(
    db: AsyncSession,
    obj_in: CiplListCreate,
    created_by: int
) -> CiplList:
    
    update_data = obj_in.model_dump(exclude_none=True)
    update_data["status"] = StatusEnum.ACTIVE
    update_data["updated_by"] = created_by

    try:
        # Check if record exists by job_number (your original upsert logic)
        result = await db.execute(
            select(CiplList).where(CiplList.job_number == obj_in.job_number)
        )
        db_obj = result.scalars().first()

        if db_obj:
            # Update existing
            for key, value in update_data.items():
                setattr(db_obj, key, value)
        else:
            # Create new
            update_data["created_by"] = created_by
            db_obj = CiplList(**update_data)
            db.add(db_obj)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    except IntegrityError as e:
        await db.rollback()
        
        error_str = str(e.orig).lower()

        # Try to extract duplicate value
        dup_value = None
        try:
            # Extract value between first two single quotes: 'SESOC2604011503'
            dup_value = str(e.orig).split("'")[1]
        except:
            dup_value = "Unknown"

        # ==================== BL_NO Duplicate ====================
        if "bl_no" in error_str:
            # Query the existing record that has this bl_no
            existing = await db.execute(
                select(CiplList).where(CiplList.bl_no == dup_value)
            )
            existing_record = existing.scalars().first()

            if existing_record:
                warning = (
                    f"BL No '{dup_value}' is already stored in "
                    f"Job Number '{existing_record.job_number}' "
                    f"and Group Number '{existing_record.group_number or 'N/A'}'. "
                    "Kindly check the provided details."
                )
            else:
                warning = f"BL No '{dup_value}' already exists. Kindly check the provided details."

            raise HTTPException(status_code=409, detail=warning)

        # ==================== GROUP_NUMBER Duplicate ====================
        elif "group_number" in error_str:
            # Query the existing record that has this group_number
            existing = await db.execute(
                select(CiplList).where(CiplList.group_number == dup_value)
            )
            existing_record = existing.scalars().first()

            if existing_record:
                warning = (
                    f"These set of CIPL (Group Number '{dup_value}') already stored "
                    f"in Job Number '{existing_record.job_number}' "
                    f"and BL No '{existing_record.bl_no or 'N/A'}'. "
                    "Kindly check the provided details."
                )
            else:
                warning = f"Group Number '{dup_value}' already exists. Kindly check the provided details."

            raise HTTPException(status_code=409, detail=warning)

        # ==================== Other duplicates (job_number, etc.) ====================
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate entry detected: {dup_value}. Please check your data."
            )

async def create_cipl_list_db2(
    db: AsyncSession,
    obj_in: CiplListCreate,
    created_by: int
) -> CiplList:

    # 🔍 Check if record already exists (adjust key if needed)
    result = await db.execute(
        select(CiplList).where(
            CiplList.job_number == obj_in.job_number
        )
    )
    db_obj = result.scalars().first()

    update_data = obj_in.model_dump(exclude_none=True)
    update_data["status"] = StatusEnum.ACTIVE
    update_data["updated_by"] = created_by

    if db_obj:
        # ✅ UPDATE existing record
        for key, value in update_data.items():
            setattr(db_obj, key, value)

    else:
        # ✅ CREATE new record
        update_data["created_by"] = created_by
        db_obj = CiplList(**update_data)
        db.add(db_obj)

    await db.commit()
    await db.refresh(db_obj)

    return db_obj

# GET ONE
async def get_cipl_list(db: AsyncSession, cipl_id: int):
    result = await db.execute(
        select(CiplList).where(CiplList.id == cipl_id)
    )
    return result.scalar_one_or_none()

# GET ALL (with pagination)
async def get_all_cipl_lists(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(CiplList).offset(skip).limit(limit)
    )
    return result.scalars().all()


# UPDATE
async def update_cipl_list1(db: AsyncSession, db_obj: CiplList, obj_in: CiplListUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# UPDATE
async def update_cipl_list(
    db: AsyncSession,
    db_obj: CiplList,
    obj_in: CiplListUpdate,
):
    update_data = obj_in.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    except IntegrityError as e:
        await db.rollback()

        error_str = str(e.orig).lower()

        # Try extracting duplicate value
        try:
            dup_value = str(e.orig).split("'")[1]
        except:
            dup_value = "Unknown"

        # ==================== BL_NO Duplicate ====================
        if "bl_no" in error_str:
            existing = await db.execute(
                select(CiplList).where(CiplList.bl_no == dup_value)
            )
            existing_record = existing.scalars().first()

            if existing_record:
                warning = (
                    f"BL No '{dup_value}' is already stored in "
                    f"Job Number '{existing_record.job_number}' "
                    f"and Group Number '{existing_record.group_number or 'N/A'}'. "
                    "Kindly check the provided details."
                )
            else:
                warning = f"BL No '{dup_value}' already exists. Kindly check the provided details."

            raise HTTPException(status_code=409, detail=warning)

        # ==================== GROUP_NUMBER Duplicate ====================
        elif "group_number" in error_str:
            existing = await db.execute(
                select(CiplList).where(CiplList.group_number == dup_value)
            )
            existing_record = existing.scalars().first()

            if existing_record:
                warning = (
                    f"These set of CIPL (Group Number '{dup_value}') already stored "
                    f"in Job Number '{existing_record.job_number}' "
                    f"and BL No '{existing_record.bl_no or 'N/A'}'. "
                    "Kindly check the provided details."
                )
            else:
                warning = f"Group Number '{dup_value}' already exists. Kindly check the provided details."

            raise HTTPException(status_code=409, detail=warning)

        # ==================== Other duplicates ====================
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate entry detected: {dup_value}. Please check your data."
            )

# DELETE (hard delete)
async def delete_cipl_list(db: AsyncSession, cipl_id: int):
    obj = await get_cipl_list(db, cipl_id)
    if not obj:
        return None

    await db.delete(obj)
    await db.commit()
    return obj

# DEACTIVATE (soft delete)
async def deactivate_cipl_list(db: AsyncSession, db_obj: CiplList, user_id: int):
    db_obj.status = StatusEnum.INACTIVE
    db_obj.updated_by = user_id

    await db.commit()
    await db.refresh(db_obj)
    return db_obj



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


async def get_commercial_invoice_by_cipl_id(
    db: AsyncSession,
    cipl_id: str
) -> Optional[Dict[str, Any]]:

    result = await db.execute(
        select(CommercialInvoice).where(CommercialInvoice.cipl_list_id == cipl_id)
    )
    obj = result.scalars().all()

    if not obj:
        return None

    return [CommercialInvoiceOut.model_validate(object).model_dump() for object in obj]


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



async def delete_commercial_invoice1(
    db: AsyncSession,
    invoice_id: int
) -> bool:

    result = await db.execute(
        delete(CommercialInvoice).where(CommercialInvoice.id == invoice_id)
    )
    await db.commit()
    

    return result.rowcount > 0


async def delete_commercial_invoice(
    db: AsyncSession,
    reference_number: str,
    cipl_id: int,
    deleted_by: int
) -> bool:

    try:
        # 1. Get invoice
        result = await db.execute(
            select(CommercialInvoice).where(
                CommercialInvoice.reference_number == reference_number
            )
        )
        invoice = result.scalars().first()

        if not invoice:
            raise HTTPException(404, "Invoice not found")

        # 2. Get CIPL List
        result = await db.execute(
            select(CiplList).where(CiplList.id == cipl_id)
        )
        cipl = result.scalars().first()

        if not cipl:
            raise HTTPException(404, "CIPL list not found")

        # 3. Update CIPL fields safely
        ref = reference_number.strip()

        # ---- ORI handling ----
        if ref.endswith("ORI") and cipl.cipl_ori:
            items = [x.strip() for x in cipl.cipl_ori.split(",") if x.strip()]
            items = [x for x in items if x != ref]
            cipl.cipl_ori = ",".join(items) if items else None

        # ---- FNL handling ----
        if ref.endswith("FNL") and cipl.cipl_fnl:
            items = [x.strip() for x in cipl.cipl_fnl.split(",") if x.strip()]
            items = [x for x in items if x != ref]
            cipl.cipl_fnl = ",".join(items) if items else None

        # ---- GROUP NUMBER handling ----
        if cipl.group_number:
            group_key = ref.split("-")[0]  # ES-00136 -> ES
            items = [x.strip() for x in cipl.group_number.split(",") if x.strip()]
            items = [x for x in items if x != group_key]
            cipl.group_number = ",".join(items) if items else None

        # Audit
        cipl.updated_by = deleted_by

        # 4. Delete invoice
        await db.delete(invoice)

        # 5. Commit transaction
        await db.commit()

        return True

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(500, f"Delete failed: {str(e)}")
    

async def delete_commercial_invoice_and_cipl_list(
    db: AsyncSession,
    cipl_id: int
) -> bool:
    try:
        # Delete child first
        result_invoice = await db.execute(
            delete(CommercialInvoice).where(CommercialInvoice.cipl_list_id == cipl_id)
        )

        # Then delete parent
        result_cipl = await db.execute(
            delete(CiplList).where(CiplList.id == cipl_id)
        )

        await db.commit()

        return (result_invoice.rowcount > 0) or (result_cipl.rowcount > 0)

    except SQLAlchemyError:
        await db.rollback()
        raise