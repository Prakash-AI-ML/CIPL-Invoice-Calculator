from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import pwd_context, verify_password
from sqlalchemy.orm import selectinload

from sqlalchemy import select, delete, text, and_
from .menu_permissions import get_menu_permissions_by_user
from .button_permissions import get_button_permissions_by_user
from typing import Dict, Any
from app.models.roles import Role
from app.models.menus import Menu, MenuPermission
from app.models.buttons import Button, ButtonPermission


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def authenticate_user1(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))  # ← Eager load role
        .filter(User.email == email, User.status == 1)
    )
    return result.scalars().first()



async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email, User.status == 1))
    return result.scalars().first()


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(
        select(User)
        .filter(User.status == 1)
        .offset(skip)
        .limit(limit)
        .order_by(User.id)
    )
    return result.scalars().all()

# app/crud/user.py


async def get_permissions_for_user(db: AsyncSession, user: User) -> Dict:
    # ALWAYS fetch fresh with eager loading — do NOT rely on user.menu_permissions
    menu_perms_result = await db.execute(
        select(MenuPermission)
        .options(selectinload(MenuPermission.menu))
        .filter(
            MenuPermission.subscribers_id == user.id,
            MenuPermission.status == 1
        )
    )
    menu_perms = menu_perms_result.scalars().all()

    button_perms_result = await db.execute(
        select(ButtonPermission)
        .options(selectinload(ButtonPermission.button), selectinload(ButtonPermission.menu))
        .filter(
            ButtonPermission.subscribers_id == user.id,
            ButtonPermission.status == 1
        )
    )
    button_perms = button_perms_result.scalars().all()

    # Build structured response with names
    menus_dict = {}
    for mp in menu_perms:
        menu_id = mp.menu_id
        if menu_id not in menus_dict:
            menus_dict[menu_id] = {
                "menu_id": menu_id,
                "menu_name": mp.menu.menu_name if mp.menu else "Unknown",
                "buttons": []
            }

    for bp in button_perms:
        menu_id = bp.menu_id
        if menu_id in menus_dict:
            menus_dict[menu_id]["buttons"].append({
                "button_id": bp.button_id,
                "button_name": bp.button.button_name if bp.button else "Unknown",
                "permission": bp.button_permission
            })

    return {
        "role": user.role.role_name if user.role else None,
        "menus": list(menus_dict.values())
    }

async def get_permissions_for_user(db: AsyncSession, user: User) -> Dict[str, Any]:
    menu_perms = await get_menu_permissions_by_user(db, user.id)
    menu_ids = [mp.menu_id for mp in menu_perms]
    
    button_perms = {}
    for menu_id in menu_ids:
        perms = await get_button_permissions_by_user_menu(db, user.id, menu_id)
        button_perms[str(menu_id)] = {bp.button_id: bp.button_permission for bp in perms}
    
    return {
        "role": user.role.role_name if user.role else None,
        "menus": menu_ids,
        "button_permissions": button_perms
    }

async def get_button_permissions_by_user_menu(db: AsyncSession, user_id: int, menu_id: int) -> List[ButtonPermission]:
    result = await db.execute(
        select(ButtonPermission).filter(
            ButtonPermission.subscribers_id == user_id,
            ButtonPermission.menu_id == menu_id,
            ButtonPermission.status == 1
        )
    )
    return result.scalars().all()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role),
                 selectinload(User.role),                    # Already had this
            selectinload(User.menu_permissions),        # ← ADD THIS
            selectinload(User.button_permissions))  # ← Eager load role
        .filter(User.email == email, User.status == 1)
    )
    return result.scalars().first()



async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))  # ← Eager load role
        .filter(User.id == user_id)
    )
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))  # ← Optional but recommended
        .filter(User.status == 1)
        .offset(skip)
        .limit(limit)
        .order_by(User.id)
    )
    return result.scalars().all()

async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.status == 1)
        .offset(skip)
        .limit(limit)
        .order_by(User.id)
    )

    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "status": user.status,
            "role": user.role.role_name if user.role else "No Role",
             "role_id": user.role_id,
            "group_id": user.group_id,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        for user in users if user.role.role_name != 'super_admin'
    ]


from datetime import datetime
async def create_user(db: AsyncSession, user: UserCreate, created_by: int) -> User:
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role_id=user.role_id,
        group_id=user.group_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        mobile = user.mobile,
        company_name = user.company_name,
        created_by = user.created_by,
        updated_by = user.updated_by
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate,
    updated_by: int
) -> Optional[User]:
    db_user = await get_user(db=db, user_id=user_id)
    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)
    # Special handling for password
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db_user.updated_by = updated_by

    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate,
    updated_by: int
) -> Optional[User]:
    db_user = await get_user(db=db, user_id=user_id)
    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)  # Only fields that were sent

    # Handle password separately and optionally
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
    elif "password" in update_data:  # Empty string or None sent
        update_data.pop("password")  # Don't set hashed_password to None

    for field, value in update_data.items():
        if field != "password":  # Already handled
            setattr(db_user, field, value)

    db_user.updated_by = updated_by

    await db.commit()
    await db.refresh(db_user)
    return db_user


async def deactivate_user(db: AsyncSession, user_id: int, updated_by: int) -> bool:
    db_user = await get_user(db=db, user_id=user_id)
    if not db_user:
        return False

    db_user.status = 0
    db_user.updated_by = updated_by
    await db.commit()
    return True


async def delete_user(
    db: AsyncSession,
    user_id: int
) -> int:
    result = await db.execute(
        delete(User)
        .where(User.id == user_id)
    )
    return result.rowcount

async def delete_user_with_permissions(db: AsyncSession, user_id: int):
    try:
        await db.execute(
            text("DELETE FROM button_permissions WHERE subscribers_id = :user_id"),
            {"user_id": user_id}
        )
        await db.execute(
            text("DELETE FROM menu_permissions WHERE subscribers_id = :user_id"),
            {"user_id": user_id}
        )
        await db.execute(
            text("DELETE FROM subscribers WHERE id = :user_id"),
            {"user_id": user_id}
        )
        await db.commit()  # Explicit commit
    except Exception as e:
        await db.rollback()  # Explicit rollback
        raise  e# Re-raise so endpoint returns 500