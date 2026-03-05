import uuid
import os
from pathlib import Path
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_order_settings import DeliveryOrder
from app.schemas.delivery_order_settings import (
    DeliveryOrderCreate,
    DeliveryOrderUpdate,
)



async def create_delivery_order(
    db: AsyncSession,
    data: DeliveryOrderCreate,
    logo_file = None,           # UploadFile or None
    created_by: int = None,
) -> DeliveryOrder:
    # Prepare data
    create_dict = data.model_dump(exclude_none=True)

    db_obj = DeliveryOrder(**create_dict)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_delivery_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[str] = None,
) -> List[DeliveryOrder]:
    stmt = select(DeliveryOrder).offset(skip).limit(limit).order_by(DeliveryOrder.id.desc())

    if client_id:
        stmt = stmt.where(DeliveryOrder.client_id == client_id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_delivery_order(db: AsyncSession, do_id: int) -> Optional[DeliveryOrder]:
    result = await db.execute(
        select(DeliveryOrder).where(DeliveryOrder.id == do_id)
    )
    return result.scalars().first()


async def update_delivery_order(
    db: AsyncSession,
    do_id: int,
    update_data: DeliveryOrderUpdate,
    logo_file = None,
) -> Optional[DeliveryOrder]:
    obj = await get_delivery_order(db, do_id)
    if not obj:
        return None

    update_dict = update_data.model_dump(exclude_none=True, exclude_unset=True)

    # Handle new logo → replace old one
    if logo_file and logo_file.filename:
        ext = Path(logo_file.filename).suffix.lower() or ".png"
        new_filename = f"{uuid.uuid4().hex}{ext}"
        new_path = LOGO_UPLOAD_DIR / new_filename

        with new_path.open("wb") as f:
            f.write(await logo_file.read())

        # Optional: delete old file
        if obj.company_logo:
            old_filename = obj.company_logo.split("/")[-1]
            old_path = LOGO_UPLOAD_DIR / old_filename
            if old_path.exists():
                os.remove(old_path)

        update_dict["company_logo"] = str(BASE_STATIC_URL + new_filename)

    for field, value in update_dict.items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)
    return obj


async def deactivate_delivery_order(
    db: AsyncSession,
    do_id: int,
    updated_by: int
) -> bool:
    obj = await get_delivery_order(db, do_id)
    if not obj:
        return False

    obj.status = 0
    obj.updated_by = updated_by
    await db.commit()
    return True


async def delete_delivery_order(db: AsyncSession, do_id: int) -> bool:
    obj = await get_delivery_order(db, do_id)
    if not obj:
        return False

    # Optional: delete logo file
    if obj.company_logo:
        filename = obj.company_logo.split("/")[-1]
        path = LOGO_UPLOAD_DIR / filename
        if path.exists():
            os.remove(path)

    await db.execute(
        delete(DeliveryOrder).where(DeliveryOrder.id == do_id)
    )
    await db.commit()
    return True