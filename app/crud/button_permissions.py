# app/crud/button_permissions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import List, Optional
from app.models.buttons import ButtonPermission
from app.schemas.buttons import ButtonPermissionCreate, ButtonPermissionUpdate, ButtonPermissionUpdate1

async def get_button_permission(db: AsyncSession, bp_id: int) -> Optional[ButtonPermission]:
    result = await db.execute(
        select(ButtonPermission)
        .filter(ButtonPermission.id == bp_id, ButtonPermission.status == 1)
    )
    return result.scalars().first()


async def get_button_permissions_by_user_menu(
    db: AsyncSession,
    user_id: int,
    menu_id: int
) -> List[ButtonPermission]:
    result = await db.execute(
        select(ButtonPermission)
        .filter(
            ButtonPermission.subscribers_id == user_id,
            ButtonPermission.menu_id == menu_id,
            ButtonPermission.status == 1
        )
    )
    return result.scalars().all()

async def get_button_permissions_by_user(
    db: AsyncSession,
    user_id: int,
    # menu_id: int
) -> List[ButtonPermission]:
    result = await db.execute(
        select(ButtonPermission)
        .filter(
            ButtonPermission.subscribers_id == user_id,
            # ButtonPermission.menu_id == menu_id,
            # ButtonPermission.status == 1
        )
    )
    return result.scalars().all()

async def create_button_permission(
    db: AsyncSession,
    bp: ButtonPermissionCreate,
    created_by: int
) -> ButtonPermission:
    db_bp = ButtonPermission(
        subscribers_id=bp.subscribers_id,
        menu_id=bp.menu_id,
        button_id=bp.button_id,
        button_permission=bp.button_permission,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_bp)
    await db.commit()
    await db.refresh(db_bp)
    return db_bp


async def update_button_permission(
    db: AsyncSession,
    bp_id: int,
    bp_update: ButtonPermissionUpdate,
    updated_by: int
) -> Optional[ButtonPermission]:
    db_bp = await get_button_permission(db=db, bp_id=bp_id)
    if not db_bp:
        return None

    update_data = bp_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bp, field, value)

    db_bp.updated_by = updated_by
    await db.commit()
    await db.refresh(db_bp)
    return db_bp



async def update_button_permission_new(
    db: AsyncSession,
    bp_update: ButtonPermissionUpdate1,
    user_id: int,
    updated_by: int
) -> Optional[ButtonPermission]:
    db_bp = await get_button_permissions_by_user(db=db, user_id=user_id)
    if not db_bp:
        return None

    update_data = bp_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bp, field, value)

    db_bp.updated_by = updated_by
    await db.commit()
    await db.refresh(db_bp)
    return db_bp


async def delete_button_permission(db: AsyncSession, bp_id: int, updated_by: int) -> bool:
    db_bp = await get_button_permission(db=db, bp_id=bp_id)
    if not db_bp:
        return False

    db_bp.status = 0
    db_bp.updated_by = updated_by
    await db.commit()
    return True

async def delete_all_button_permissions_for_user(
    db: AsyncSession,
    user_id: int
) -> int:
    """
    Soft-deletes ALL button permissions for a given user.
    Returns number of rows affected.
    """
    # result = await db.execute(
    #     update(ButtonPermission)
    #     .where(ButtonPermission.subscribers_id == user_id)
    #     .values(
    #         status=0,
    #         updated_by=updated_by,
    #         updated_at=datetime.now()
    #     )
    # )
    # return result.rowcount
    result = await db.execute(
        delete(ButtonPermission)
        .where(ButtonPermission.subscribers_id == user_id)
    )
    await db.commit()  # Make sure to commit the changes
    return result.rowcount