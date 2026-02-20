# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict
from app.db.session import get_db
from sqlalchemy import select
from app.crud.user import get_user_by_email
from app.core.security import verify_token
from app.models.user import User
from app.db.session import get_db
from app.models.user import User
from app.models.menus import MenuPermission
from app.models.buttons import ButtonPermission
from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import get_db
from app.crud.user import get_user_by_email  # your async CRUD
# from app.core.security import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    email: str = payload.email
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # ← ADD await HERE!
    user = await get_user_by_email(db=db, email=email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(required_role: str):
    async def role_checker(current_user = Depends(get_current_user)):
        # Now current_user is properly awaited → has .role
        if not current_user.role:
            raise HTTPException(status_code=403, detail="User has no role assigned")
        
        if current_user.role.role_name != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return current_user
    return role_checker


# app/api/dependencies.py
from sqlalchemy.orm import selectinload, with_loader_criteria

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None or (email := payload.email) is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    # ← Use the same eager-loaded version
    user = await get_user_by_email(db=db, email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

async def get_user_permissions_detailed_old(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.email  # ← Use .get() since payload is dict
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # CORRECT eager loading
    
    result = await db.execute(
    select(User)
    .options(
        selectinload(User.role),
        selectinload(User.menu_permissions).selectinload(MenuPermission.menu),
        selectinload(User.button_permissions).selectinload(ButtonPermission.menu),
        selectinload(User.button_permissions).selectinload(ButtonPermission.button),
        with_loader_criteria(MenuPermission, MenuPermission.status == 1),
        with_loader_criteria(ButtonPermission, ButtonPermission.status == 1),
    )
    .filter(User.email == email, User.status == 1)
)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.role_name if user.role else "No Role"

    menus: Dict[str, Dict] = {}
    for mp in user.menu_permissions:
        menu_name = mp.menu.menu_name if mp.menu else "Unknown Menu"
        menus.setdefault(menu_name, {"buttons": []})

    for bp in user.button_permissions:
        menu_name = bp.menu.menu_name if bp.menu else "Unknown Menu"
        button_name = bp.button.button_name if bp.button else "Unknown Button"

        if menu_name in menus:
            menus[menu_name]["buttons"].append({
                "button_name": button_name,
                "permission": bp.button_permission,
                "status": bp.status
            })

    return {
        "user_id": user.id,
        "username":user.username,
        "role": role_name,
        "email":user.email,
        "profile": user.profile_path if user.profile_path else "default-profile.png",
        "logo": user.company_logo if user.company_logo else "default-profile.png",
        "menus": menus
    }


async def get_user_permissions_detailed(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    token = credentials.credentials
    payload = verify_token(token)
    

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    email = payload.email  # Standard JWT sub claim (email)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing sub",
        )

    # Check if this is an impersonated session
    is_impersonated = payload.impersonated
    impersonated_by_id = payload.impersonated_by  # original super admin user_id

    # Load the CURRENT user (the one actually logged in now — could be impersonated)
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.menu_permissions).selectinload(MenuPermission.menu),
            selectinload(User.button_permissions).selectinload(ButtonPermission.menu),
            selectinload(User.button_permissions).selectinload(ButtonPermission.button),
            with_loader_criteria(MenuPermission, MenuPermission.status == 1),
            with_loader_criteria(ButtonPermission, ButtonPermission.status == 1),
        )
        .where(User.email == email, User.status == 1)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.role_name if user.role else "No Role"

    # Determine permissions
    can_impersonate = (role_name.lower() == "super_admin")

    # Build menu permissions
    menus: Dict[str, Dict] = {}
    for mp in user.menu_permissions:
        menu_name = mp.menu.menu_name if mp.menu else "Unknown Menu"
        menus.setdefault(menu_name, {"buttons": []})

    for bp in user.button_permissions:
        menu_name = bp.menu.menu_name if bp.menu else "Unknown Menu"
        button_name = bp.button.button_name if bp.button else "Unknown Button"

        if menu_name in menus:
            menus[menu_name]["buttons"].append({
                "button_name": button_name,
                "permission": bp.button_permission,
                "status": bp.status
            })

    return {
        "user_id": user.id,
        "username": user.username,
        "role": role_name,
        "email": user.email,
        "profile": user.profile_path or "default-profile.png",
        "logo": user.company_logo or "default-logo.png",

        # New impersonation-related fields
        "can_impersonate": can_impersonate,           # Only true for super admin
        "impersonated": is_impersonated,              # True if currently impersonating someone
        "impersonated_by": impersonated_by_id,        # ID of original super admin (if impersonating)

        "menus": menus
    }

def check_menu_permission(
    current_user,
    menu_name: str,
):
    # Check if user has access to the menu
    if not current_user['menus']:
        raise HTTPException(status_code=403, detail=f"Access to menu {menu_name} denied")
    user_menus = current_user['menus'].keys() if current_user['menus'] else None
    if menu_name.lower() not in user_menus:
        raise HTTPException(status_code=403, detail=f"Access to menu {menu_name} denied")
    return True


def check_button_permission(
    current_user,
    menu_name: str,
    required_button: str
):
    # Check if user has access to the menu
    user_button =[data['button_name'] for data in current_user['menus'][menu_name]['buttons']] if current_user['menus'] else None
    
    if required_button.lower() not in user_button:
        raise HTTPException(status_code=403, detail=f"Button permission '{required_button}' denied on menu {menu_name}")
    return True

