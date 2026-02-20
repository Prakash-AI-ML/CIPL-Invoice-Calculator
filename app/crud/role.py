# app/crud/roles.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
from app.models.user import User
from app.models.roles import Role 
from app.schemas.roles import RoleCreate


async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Role).where(Role.role_name != 'super_admin').offset(skip).limit(limit))
    return result.scalars().all()

async def create_role(db: AsyncSession, role: RoleCreate):
    db_role = Role(**role.dict())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role


 # or from app.models import Role

async def get_role(db: AsyncSession, role_id: int) -> Optional[Role]:
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalars().first()


async def update_role(db: AsyncSession, role_id: int, role_update: dict) -> Optional[Role]:
    # ← MUST await get_role!
    db_role = await get_role(db=db, role_id=role_id)
    if not db_role:
        return None

    update_data = role_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_role, field, value)

    # Optional: explicitly mark as modified if needed (usually not required in async)
    await db.commit()
    await db.refresh(db_role)
    return db_role


async def deactivate_role(db: AsyncSession, role_id: int, updated_by: int) -> bool:
    # ← MUST await get_role!
    db_role = await get_role(db=db, role_id=role_id)
    if not db_role:
        return False

    db_role.status = 0
    db_role.updated_by = updated_by

    await db.commit()
    return True

async def delete_role(db: AsyncSession, role_id: int):
    # 1️⃣ Find users assigned to this role
    result = await db.execute(
        select(User.id, User.username, User.email)
        .where(User.role_id == role_id)
    )
    users = result.all()

    # 2️⃣ If users exist → block deletion
    if users:
        return {
            "can_delete": False,
            "users": [
                {"id": u.id, "username": u.username, "email": u.email}
                for u in users
            ]
        }

    # 3️⃣ No users → safe to delete
    role_result = await db.execute(
        delete(Role).where(Role.id == role_id)
    )

    if role_result.rowcount == 0:
        return None  # role not found

    await db.commit()
    return {"can_delete": True}
