# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from app.schemas.roles import RoleBase, RoleCreate, RoleResponse, RoleUpdate
from app.schemas.user import *
from app.schemas.menus import MenuBase, MenuCreate, MenuPermissionBase, MenuPermissionCreate, MenuPermissionResponse, MenuPermissionUpdate, MenuResponse, MenuUpdate
from app.schemas.buttons import ButtonBase, ButtonCreate, ButtonPermissionBase, ButtonPermissionCreate, ButtonPermissionResponse, ButtonPermissionUpdate, ButtonResponse, ButtonUpdate
# from .security import from pwd_context, ALGORITHM, SECRET_KEY
from app.core.config import settings
from app.models.user import User
from app.models.roles import Role
from app.models.menus import MenuPermission, Menu
from app.models.buttons import ButtonPermission, Button

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Role CRUD
def create_role(db: Session, role: RoleCreate) -> Role:
    db_role = Role(**role.dict())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id == role_id, Role.status == 1).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    return db.query(Role).filter(Role.status == 1).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: int, role_update: RoleUpdate) -> Optional[Role]:
    db_role = get_role(db, role_id)
    if db_role:
        update_data = role_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)
        db.commit()
        db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int, updated_by: int) -> bool:
    db_role = get_role(db, role_id)
    if db_role:
        db_role.status = 0
        db_role.updated_by = updated_by
        db.commit()
        return True
    return False

# Menu CRUD
def create_menu(db: Session, menu: MenuCreate) -> Menu:
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

def get_menu(db: Session, menu_id: int) -> Optional[Menu]:
    return db.query(Menu).filter(Menu.id == menu_id, Menu.status == 1).first()

def get_menus(db: Session, skip: int = 0, limit: int = 100) -> List[Menu]:
    return db.query(Menu).filter(Menu.status == 1).offset(skip).limit(limit).all()

def update_menu(db: Session, menu_id: int, menu_update: MenuUpdate) -> Optional[Menu]:
    db_menu = get_menu(db, menu_id)
    if db_menu:
        update_data = menu_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_menu, field, value)
        db.commit()
        db.refresh(db_menu)
    return db_menu

def delete_menu(db: Session, menu_id: int, updated_by: int) -> bool:
    db_menu = get_menu(db, menu_id)
    if db_menu:
        db_menu.status = 0
        db_menu.updated_by = updated_by
        db.commit()
        return True
    return False

# Button CRUD
def create_button(db: Session, button: ButtonCreate) -> Button:
    db_button = Button(**button.dict())
    db.add(db_button)
    db.commit()
    db.refresh(db_button)
    return db_button

def get_button(db: Session, button_id: int) -> Optional[Button]:
    return db.query(Button).filter(Button.id == button_id, Button.status == 1).first()

def get_buttons(db: Session, skip: int = 0, limit: int = 100) -> List[Button]:
    return db.query(Button).filter(Button.status == 1).offset(skip).limit(limit).all()

def update_button(db: Session, button_id: int, button_update: ButtonUpdate) -> Optional[Button]:
    db_button = get_button(db, button_id)
    if db_button:
        update_data = button_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_button, field, value)
        db.commit()
        db.refresh(db_button)
    return db_button

def delete_button(db: Session, button_id: int, updated_by: int) -> bool:
    db_button = get_button(db, button_id)
    if db_button:
        db_button.status = 0
        db_button.updated_by = updated_by
        db.commit()
        return True
    return False

# MenuPermission CRUD
def create_menu_permission(db: Session, mp: MenuPermissionCreate) -> MenuPermission:
    db_mp = MenuPermission(**mp.dict())
    db.add(db_mp)
    db.commit()
    db.refresh(db_mp)
    return db_mp

def get_menu_permission(db: Session, mp_id: int) -> Optional[MenuPermission]:
    return db.query(MenuPermission).filter(MenuPermission.id == mp_id, MenuPermission.status == 1).first()

def get_menu_permissions_by_role(db: Session, role_id: int) -> List[MenuPermission]:
    return db.query(MenuPermission).filter(
        MenuPermission.role_id == role_id,
        MenuPermission.status == 1
    ).all()

def update_menu_permission(db: Session, mp_id: int, mp_update: MenuPermissionUpdate) -> Optional[MenuPermission]:
    db_mp = get_menu_permission(db, mp_id)
    if db_mp:
        update_data = mp_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_mp, field, value)
        db.commit()
        db.refresh(db_mp)
    return db_mp

def delete_menu_permission(db: Session, mp_id: int, updated_by: int) -> bool:
    db_mp = get_menu_permission(db, mp_id)
    if db_mp:
        db_mp.status = 0
        db_mp.updated_by = updated_by
        db.commit()
        return True
    return False

# ButtonPermission CRUD
def create_button_permission(db: Session, bp: ButtonPermissionCreate) -> ButtonPermission:
    db_bp = ButtonPermission(**bp.dict())
    db.add(db_bp)
    db.commit()
    db.refresh(db_bp)
    return db_bp

def get_button_permission(db: Session, bp_id: int) -> Optional[ButtonPermission]:
    return db.query(ButtonPermission).filter(ButtonPermission.id == bp_id, ButtonPermission.status == 1).first()

def get_button_permissions_by_role_menu(db: Session, role_id: int, menu_id: int) -> List[ButtonPermission]:
    return db.query(ButtonPermission).filter(
        ButtonPermission.role_id == role_id,
        ButtonPermission.menu_id == menu_id,
        ButtonPermission.status == 1
    ).all()

def update_button_permission(db: Session, bp_id: int, bp_update: ButtonPermissionUpdate) -> Optional[ButtonPermission]:
    db_bp = get_button_permission(db, bp_id)
    if db_bp:
        update_data = bp_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bp, field, value)
        db.commit()
        db.refresh(db_bp)
    return db_bp

def delete_button_permission(db: Session, bp_id: int, updated_by: int) -> bool:
    db_bp = get_button_permission(db, bp_id)
    if db_bp:
        db_bp.status = 0
        db_bp.updated_by = updated_by
        db.commit()
        return True
    return False

# User CRUD
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email, User.status == 1).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role_id=user.role_id,
        created_by=user.created_by
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id, User.status == 1).first()

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int, updated_by: int) -> bool:
    db_user = get_user(db, user_id)
    if db_user:
        db_user.status = 0
        db_user.updated_by = updated_by
        db.commit()
        return True
    return False

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def get_permissions_for_user(db: Session, user: User) -> Dict[str, Any]:
    menu_perms = get_menu_permissions_by_role(db, user.role_id)
    menu_ids = [mp.menu_id for mp in menu_perms]
    button_perms = {}
    for menu_id in menu_ids:
        perms = get_button_permissions_by_role_menu(db, user.role_id, menu_id)
        button_perms[str(menu_id)] = {bp.button_id: bp.button_permission for bp in perms}
    
    return {
        "role": user.role.role_name,
        "menu_permissions": menu_ids,
        "button_permissions": button_perms
    }

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None
    

# Replace get_menu_permissions_by_role with user-based
def get_menu_permissions_by_user(db: Session, user_id: int) -> List[MenuPermission]:
    return db.query(MenuPermission).filter(
        MenuPermission.subscribers_id == user_id,
        MenuPermission.status == 1
    ).all()

def get_button_permissions_by_user_menu(db: Session, user_id: int, menu_id: int) -> List[ButtonPermission]:
    return db.query(ButtonPermission).filter(
        ButtonPermission.subscribers_id == user_id,
        ButtonPermission.menu_id == menu_id,
        ButtonPermission.status == 1
    ).all()

# Update get_permissions_for_user
def get_permissions_for_user(db: Session, user: User) -> Dict[str, Any]:
    menu_perms = get_menu_permissions_by_user(db, user.id)
    menu_ids = [mp.menu_id for mp in menu_perms]
    
    button_perms = {}
    for menu_id in menu_ids:
        perms = get_button_permissions_by_user_menu(db, user.id, menu_id)
        button_perms[str(menu_id)] = {bp.button_id: bp.button_permission for bp in perms}
    
    return {
        "role": user.role.role_name if user.role else None,
        "menu_permissions": menu_ids,
        "button_permissions": button_perms
    }


# app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any


from jose import JWTError, jwt
from datetime import datetime, timedelta
import json

# Role CRUD
async def create_role(db: AsyncSession, role: RoleCreate) -> Role:
    db_role = Role(**role.dict())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role

async def get_role(db: AsyncSession, role_id: int) -> Optional[Role]:
    result = await db.execute(
        select(Role).filter(Role.id == role_id, Role.status == 1)
    )
    return result.scalars().first()

async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Role]:
    result = await db.execute(
        select(Role).filter(Role.status == 1).offset(skip).limit(limit)
    )
    return result.scalars().all()

# MenuPermission CRUD (updated for subscribers_id)
async def get_menu_permissions_by_user(db: AsyncSession, user_id: int) -> List[MenuPermission]:
    result = await db.execute(
        select(MenuPermission).filter(
            MenuPermission.subscribers_id == user_id,
            MenuPermission.status == 1
        )
    )
    return result.scalars().all()

async def get_button_permissions_by_user_menu(db: AsyncSession, user_id: int, menu_id: int) -> List[ButtonPermission]:
    result = await db.execute(
        select(ButtonPermission).filter(
            ButtonPermission.subscribers_id == user_id,
            ButtonPermission.menu_id == menu_id,
            ButtonPermission.status == 1
        )
    )
    return result.scalars().all()

async def get_permissions_for_user(db: AsyncSession, user: User) -> Dict[str, Any]:
    menu_perms = await get_menu_permissions_by_user(db, user.id)
    menu_ids = [mp.menu_id for mp in menu_perms]
    
    button_perms = {}
    for menu_id in menu_ids:
        perms = await get_button_permissions_by_user_menu(db, user.id, menu_id)
        button_perms[str(menu_id)] = {bp.button_id: bp.button_permission for bp in perms}
    
    return {
        "role": user.role.role_name if user.role else None,
        "menu_permissions": menu_ids,
        "button_permissions": button_perms
    }

# User CRUD
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).filter(User.email == email, User.status == 1)
    )
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


from sqlalchemy.orm import selectinload  # or joinedload

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))  # <--- Eager load role
        .filter(User.email == email, User.status == 1)
    )
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))  # <--- Eager load role
        .filter(User.id == user_id, User.status == 1)
    )
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


async def get_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Role).offset(skip).limit(limit))
    return result.scalars().all()

async def create_role(db: AsyncSession, role: RoleCreate):
    db_role = Role(**role.dict())
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role


# app/crud/roles.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from app.models.roles import Role  # or from app.models import Role

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


async def delete_role(db: AsyncSession, role_id: int, updated_by: int) -> bool:
    # ← MUST await get_role!
    db_role = await get_role(db=db, role_id=role_id)
    if not db_role:
        return False

    db_role.status = 0
    db_role.updated_by = updated_by

    await db.commit()
    return True