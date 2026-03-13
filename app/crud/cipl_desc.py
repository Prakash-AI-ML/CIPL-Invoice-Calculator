from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cipl_desc import StatusEnum
from app.models.cipl_desc import CiplDesc
from app.schemas.cipl_desc import (
    CiplDescCreate,
    CiplDescUpdate,
)

async def create_cipl_desc(
    db: AsyncSession,
    data: CiplDescCreate,
    created_by: int
) -> CiplDesc:

    create_dict = data.model_dump(exclude_none=True)
    create_dict["created_by"] = created_by
    create_dict["updated_by"] = created_by

    db_obj = CiplDesc(**create_dict)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    return db_obj


async def get_cipl_descs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    item_id: Optional[int] = None,
) -> List[CiplDesc]:

    stmt = select(CiplDesc).offset(skip).limit(limit).order_by(CiplDesc.id.desc())

    if item_id:
        stmt = stmt.where(CiplDesc.item_id == item_id)

    result = await db.execute(stmt)

    return result.scalars().all()

async def get_cipl_desc(
    db: AsyncSession,
    desc_id: int
) -> Optional[CiplDesc]:

    result = await db.execute(
        select(CiplDesc).where(CiplDesc.id == desc_id)
    )

    return result.scalars().first()


async def update_cipl_desc(
    db: AsyncSession,
    desc_id: int,
    update_data: CiplDescUpdate,
    updated_by: int
) -> Optional[CiplDesc]:

    obj = await get_cipl_desc(db, desc_id)

    if not obj:
        return None

    update_dict = update_data.model_dump(
        exclude_none=True,
        exclude_unset=True
    )

    update_dict["updated_by"] = updated_by

    for field, value in update_dict.items():
        setattr(obj, field, value)

    await db.commit()
    await db.refresh(obj)

    return obj


async def deactivate_cipl_desc(
    db: AsyncSession,
    desc_id: int,
    updated_by: int
) -> bool:

    obj = await get_cipl_desc(db, desc_id)

    if not obj:
        return False

    obj.status = StatusEnum.INACTIVE
    obj.updated_by = updated_by

    await db.commit()

    return True



async def delete_cipl_desc(
    db: AsyncSession,
    desc_id: int
) -> bool:

    obj = await get_cipl_desc(db, desc_id)

    if not obj:
        return False

    await db.execute(
        delete(CiplDesc).where(CiplDesc.id == desc_id)
    )

    await db.commit()

    return True