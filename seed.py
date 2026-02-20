import asyncio
from app.db.session import get_db
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import UserRole
from app.core.config import engine
from app.db.base_class import Base


async def seed_super_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Ensure tables
    async for db in get_db():
        user = UserCreate(
            full_name="Muhun",
            username="muhun",
            email="muhun@gfs.com",
            password="123456",
            role=UserRole.super_admin,
            group_id= 1
        )
        created = await create_user(db, user)
        print(f"Created: {created}")

asyncio.run(seed_super_admin())


# from app.core.security import get_password_hash
# print(get_password_hash("test"))  # Should print a $2b$... hash without error