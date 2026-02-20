# app/crud/menus.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from app.models.menus import Menu
from app.schemas.menus import MenuCreate, MenuUpdate

async def get_menu(db: AsyncSession, menu_id: int) -> Optional[Menu]:
    result = await db.execute(
        select(Menu).filter(Menu.id == menu_id)
    )
    return result.scalars().first()


async def get_menus(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Menu]:
    result = await db.execute(
        select(Menu)
        .filter(Menu.status == 1)
        .offset(skip)
        .limit(limit)
        .order_by(Menu.id)
    )
    return result.scalars().all()


async def create_menu(db: AsyncSession, menu: MenuCreate, created_by: int) -> Menu:
    db_menu = Menu(
        menu_name=menu.menu_name,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_menu)
    await db.commit()
    await db.refresh(db_menu)
    return db_menu


async def update_menu(
    db: AsyncSession,
    menu_id: int,
    menu_update: MenuUpdate,
    updated_by: int
) -> Optional[Menu]:
    db_menu = await get_menu(db=db, menu_id=menu_id)
    if not db_menu:
        return None

    update_data = menu_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_menu, field, value)

    db_menu.updated_by = updated_by

    await db.commit()
    await db.refresh(db_menu)
    return db_menu


async def deactivate_menu(db: AsyncSession, menu_id: int, updated_by: int) -> bool:
    db_menu = await get_menu(db=db, menu_id=menu_id)
    if not db_menu:
        return False

    db_menu.status = 0
    db_menu.updated_by = updated_by
    await db.commit()
    return True

async def delete_menu(db: AsyncSession, menu_id: int) -> bool:
    db_menu = await db.execute(
        delete(Menu)
        .where(Menu.id == menu_id)
    )
    if not db_menu:
        return False

   
    return f'Deleted menu {menu_id}'