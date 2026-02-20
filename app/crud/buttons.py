# app/crud/buttons.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from app.models.buttons import Button
from app.schemas.buttons import ButtonCreate, ButtonUpdate

async def get_button(db: AsyncSession, button_id: int) -> Optional[Button]:
    result = await db.execute(
        select(Button).filter(Button.id == button_id)
    )
    return result.scalars().first()


async def get_buttons(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Button]:
    result = await db.execute(
        select(Button)
        .filter(Button.status == 1)
        .offset(skip)
        .limit(limit)
        .order_by(Button.id)
    )
    return result.scalars().all()


async def create_button(db: AsyncSession, button: ButtonCreate, created_by: int) -> Button:
    db_button = Button(
        button_name=button.button_name,
        created_by=created_by,
        updated_by=created_by
    )
    db.add(db_button)
    await db.commit()
    await db.refresh(db_button)
    return db_button


async def update_button(
    db: AsyncSession,
    button_id: int,
    button_update: ButtonUpdate,
    updated_by: int
) -> Optional[Button]:
    db_button = await get_button(db=db, button_id=button_id)
    if not db_button:
        return None

    update_data = button_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_button, field, value)

    db_button.updated_by = updated_by

    await db.commit()
    await db.refresh(db_button)
    return db_button


async def deactivate_button(db: AsyncSession, button_id: int, updated_by: int) -> bool:
    db_button = await get_button(db=db, button_id=button_id)
    if not db_button:
        return False

    db_button.status = 0
    db_button.updated_by = updated_by
    await db.commit()
    return True

async def delete_button(db: AsyncSession, button_id: int) -> bool:
    db_button = await db.execute(
        delete(Button)
        .where(Button.id == button_id)
    )

    
    if not db_button:
        return False

    return f'Deleted button {button_id}'