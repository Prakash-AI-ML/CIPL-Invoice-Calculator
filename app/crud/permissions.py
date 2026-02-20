# app/crud/permissions.py
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import Dict
from app.db.session import get_db
from app.models.user import User
from app.models.menus import MenuPermission
from app.models.buttons import ButtonPermission
from app.core.security import verify_token  # Your JWT verify function

security = HTTPBearer()

async def get_user_permissions_detailed1(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Input: HTTPAuthorizationCredentials (from header)
    Output: Detailed permissions with menu names and button names + permissions
    {
        "subscriber_id": int,
        "role_name": str,
        "menus": {
            "Client": {
                "buttons": [
                    {"button_name": "View", "permission": "view"},
                    {"button_name": "Add", "permission": "add"}
                ]
            },
            "Dashboard": { ... }
        }
    }
    Raises 401 if token invalid or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials"
        )

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Fetch user with all relationships eager-loaded
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.menu_permissions).selectinload(MenuPermission.menu),
            selectinload(User.button_permissions)
                .selectinload(ButtonPermission.menu)
                .selectinload(ButtonPermission.button)
        )
        .filter(User.email == email, User.status == 1)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Build structured permissions
    role_name = user.role.role_name if user.role else "No Role"

    menus = {}
    for mp in user.menu_permissions:
        menu_name = mp.menu.menu_name if mp.menu else "Unknown Menu"
        if menu_name not in menus:
            menus[menu_name] = {"buttons": []}

    for bp in user.button_permissions:
        menu_name = bp.menu.menu_name if bp.menu else "Unknown Menu"
        button_name = bp.button.button_name if bp.button else "Unknown Button"

        if menu_name in menus:
            menus[menu_name]["buttons"].append({
                "button_name": button_name,
                "permission": bp.button_permission
            })

    return {
        "subscriber_id": user.id,
        "role_name": role_name,
        "menus": menus
    }


async def get_user_permissions_detailed(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Input: HTTPAuthorizationCredentials
    Output: Detailed permissions with menu names and button names + permissions
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # FIX: If payload is TokenData (Pydantic model), access attributes directly
    if hasattr(payload, "sub"):
        email = payload.sub
    elif isinstance(payload, dict):
        email = payload.get("sub")
    else:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Fetch user with all relationships eager-loaded
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.menu_permissions).selectinload(MenuPermission.menu),
            selectinload(User.button_permissions)
                .selectinload(ButtonPermission.menu)
                .selectinload(ButtonPermission.button)
        )
        .filter(User.email == email, User.status == 1)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Build structured permissions
    role_name = user.role.role_name if user.role else "No Role"

    menus = {}
    for mp in user.menu_permissions:
        menu_name = mp.menu.menu_name if mp.menu else "Unknown Menu"
        if menu_name not in menus:
            menus[menu_name] = {"buttons": []}

    for bp in user.button_permissions:
        menu_name = bp.menu.menu_name if bp.menu else "Unknown Menu"
        button_name = bp.button.button_name if bp.button else "Unknown Button"

        if menu_name in menus:
            menus[menu_name]["buttons"].append({
                "button_name": button_name,
                "permission": bp.button_permission
            })

    return {
        "subscriber_id": user.id,
        "role_name": role_name,
        "menus": menus
    }