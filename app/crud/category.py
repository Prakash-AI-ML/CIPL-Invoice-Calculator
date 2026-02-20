from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from typing import Optional
from app.models.user import User
from app.models.category import Category 
from app.schemas.category import CategoryCreate


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Category).offset(skip).limit(limit))
    return result.scalars().all()

async def create_category(db: AsyncSession, category: CategoryCreate):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


 # or from app.models import Role

async def get_category(db: AsyncSession, category_id: int) -> Optional[Category]:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalars().first()


async def update_category(db: AsyncSession, category_id: int, category_update: dict) -> Optional[Category]:
    # ← MUST await get_category!
    db_category = await get_category(db=db, category_id=category_id)
    if not db_category:
        return None

    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    # Optional: explicitly mark as modified if needed (usually not required in async)
    await db.commit()
    await db.refresh(db_category)
    return db_category


async def deactivate_category(db: AsyncSession, category_id: int, updated_by: int) -> bool:
    # ← MUST await get_category!
    db_category = await get_category(db=db, category_id=category_id)
    if not db_category:
        return False

    db_category.status = 0
    db_category.updated_by = updated_by

    await db.commit()
    return True

async def delete_category(db: AsyncSession, category_id: int, category_name: str):
    # 1️⃣ Find users assigned to this role
    query = text("SELECT id, name,  merchant_category FROM client_details WHERE merchant_category LIKE :merchant_category")
    result = await db.execute(query, {"merchant_category": f"%{category_name}%"} )
    category = result.all()


    # 2️⃣ If users exist → block deletion
    if category:
        return {
            "can_delete": False,
            "clients": [
                {"id": c.id, "client_name": c.name, "merchant_category": c.merchant_category}
                for c in category
            ]
        }

    # 3️⃣ No users → safe to delete
    category_result = await db.execute(
        delete(Category).where(Category.id == category_id)
    )

    if category_result.rowcount == 0:
        return None  # role not found

    await db.commit()
    return {"can_delete": True}
