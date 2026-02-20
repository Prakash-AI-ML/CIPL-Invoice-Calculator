# app/crud/menu_permissions.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from typing import List, Optional
from app.models.menus import MenuPermission
from app.schemas.menus import MenuPermissionCreate, MenuPermissionUpdate, MenuPermissionUpdate1

async def get_menu_permission(db: AsyncSession, mp_id: int) -> Optional[MenuPermission]:
    result = await db.execute(
        select(MenuPermission)
        .filter(MenuPermission.id == mp_id,
                #  MenuPermission.status == 1
                 )
    )
    return result.scalars().first()


async def get_menu_permissions_by_user(
    db: AsyncSession,
    user_id: int
) -> List[MenuPermission]:
    result = await db.execute(
        select(MenuPermission)
        .filter(
            MenuPermission.subscribers_id == user_id,
            # MenuPermission.status == 1
        )
    )
    return result.scalars().all()


async def create_menu_permission(
    db: AsyncSession,
    mp: MenuPermissionCreate,
    created_by: int
) -> MenuPermission:
    db_mp = MenuPermission(
        subscribers_id=mp.subscribers_id,
        menu_id=mp.menu_id,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_mp)
    await db.commit()
    await db.refresh(db_mp)
    return db_mp


async def update_menu_permission(
    db: AsyncSession,
    mp_id: int,
    mp_update: MenuPermissionUpdate,
    updated_by: int
) -> Optional[MenuPermission]:
    db_mp = await get_menu_permission(db=db, mp_id=mp_id)
    if not db_mp:
        return None

    update_data = mp_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_mp, field, value)

    db_mp.updated_by = updated_by
    await db.commit()
    await db.refresh(db_mp)
    return db_mp

async def update_menu_permission_new(
    db: AsyncSession,
    mp_update: MenuPermissionUpdate1,
    user_id:int,
    updated_by: int
) -> Optional[MenuPermission]:
    db_mp = await get_menu_permissions_by_user(db=db, user_id=user_id)
    if not db_mp:
        return None

    update_data = mp_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_mp, field, value)

    db_mp.updated_by = updated_by
    await db.commit()
    await db.refresh(db_mp)
    return db_mp


async def delete_menu_permission(db: AsyncSession, mp_id: int, updated_by: int) -> bool:
    db_mp = await get_menu_permission(db=db, mp_id=mp_id)
    if not db_mp:
        return False

    db_mp.status = 0
    db_mp.updated_by = updated_by
    await db.commit()
    return True


async def delete_all_menu_permissions_for_user(
    db: AsyncSession,
    user_id: int,
) -> int:
    """
    Soft-deletes ALL menu permissions for a given user.
    Returns number of rows affected.
    """
    result = await db.execute(
        delete(MenuPermission)
        .where(MenuPermission.subscribers_id == user_id)
        
    )
    
    return result.rowcount