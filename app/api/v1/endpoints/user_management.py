# app/routers/users.py (or a new file like user_management.py)
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update 
from sqlalchemy.orm import selectinload
import os
import uuid
from typing import Optional

from app.db.session import get_db
from app.crud.user import create_user, update_user as crud_update_user, delete_user_with_permissions
from app.crud.menu_permissions import create_menu_permission, delete_all_menu_permissions_for_user
from app.crud.button_permissions import create_button_permission, delete_all_button_permissions_for_user
from app.models.user import User
# from app.api.deps import get_current_user, require_role
from app.api.dependencies import get_user_permissions_detailed
from app.core.config import settings
from app.schemas.user_management import UserManageRequest, UserManageResponse, PermissionDetail, ButtonPermissionDetail
from app.schemas.menus import MenuPermissionCreate, MenuPermissionUpdate1
from app.schemas.buttons import ButtonPermissionCreate, ButtonPermissionUpdate1
from app.schemas.user import UserCreate, UserUpdate
from app.models.menus import MenuPermission
from app.models.buttons import ButtonPermission
from app.crud.log_manage import backend_logs


router = APIRouter()

STATIC_DIR = r"app/static/app/images"
PROFILE_DIR = os.path.join(STATIC_DIR, "profiles")
LOGO_DIR = os.path.join(STATIC_DIR, "logos")

# Create directories if they don't exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(LOGO_DIR, exist_ok=True)


def generate_filename(original_filename: str) -> str:
    """Generate 16-char UUID + original extension"""
    ext = os.path.splitext(original_filename)[1].lower()  # e.g., .jpg
    if not ext:
        ext = ".png"  # fallback
    uuid_part = uuid.uuid4().hex[:16]  # 16 characters
    return f"{uuid_part}{ext}"

@router.post("/manage", response_model=dict)
async def manage_user(
    request: Request,
    data: UserManageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    """
    Create or update a user with menu and button permissions in one request.
    """
    subscriber_data = data.subscriber
    description = f" Create or update a user with menu and button permissions accessed by authenticated user: {current_user['username']} "
    action = 'Uses Management' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/user/manage',
                        action= action, description= description, is_backend= True, input_params= data.model_dump())

    if data.update:
        if not data.subscriber_id:
            raise HTTPException(status_code=400, detail="subscriber_id required for update")
        user_id = data.subscriber_id

        # Update existing user
        update_user_data = UserUpdate(username=subscriber_data.username,
            email=subscriber_data.email,
            password=subscriber_data.password,
            role_id=subscriber_data.role_id,
            group_id=subscriber_data.group_id,
            status=subscriber_data.status,
            updated_by=subscriber_data.updated_by,
            company_name= subscriber_data.company,
            mobile= subscriber_data.mobile)
        updated_user = await crud_update_user(
            db=db,
            user_id=user_id,
            user_update=update_user_data,
            updated_by=subscriber_data.updated_by
        )
        await delete_all_menu_permissions_for_user(db=db, user_id=user_id)
        await delete_all_button_permissions_for_user(db=db, user_id=user_id)
    else:
        # Create new user
        if not subscriber_data.password:
            raise HTTPException(status_code=400, detail="password required for new user")
        new_user_data = UserCreate(username=subscriber_data.username,
            email=subscriber_data.email,
            password=subscriber_data.password,
            role_id=subscriber_data.role_id,
            group_id=subscriber_data.group_id,
            created_by=subscriber_data.created_by,
            updated_by=subscriber_data.updated_by,
            company_name= subscriber_data.company,
            mobile= subscriber_data.mobile

            )
        new_user = await create_user(
            db=db,
            user = new_user_data,
            created_by=subscriber_data.created_by
        )
        user_id = new_user.id

    # Now assign menu and button permissions using the final user_id
    created_permissions = {"menu": [], "button": []}

    # Menu Permissions
    for mp in data.menu_permission:
        mp_data = MenuPermissionCreate(subscribers_id=user_id,
            menu_id=mp.menu_id,
            status=mp.status,
            created_by=mp.created_by)
        mp_created = await create_menu_permission(
            db=db,
            mp = mp_data,
            created_by=mp.created_by
        )
        created_permissions["menu"].append({
            "id": mp_created.id,
            "menu_id": mp_created.menu_id
        })

    # Button Permissions
    for bp in data.button_permission:
        bp_data = ButtonPermissionCreate(subscribers_id=user_id,
                                        menu_id=bp.menu_id,
                                        button_id=bp.button_id,
                                        button_permission=bp.button_permission,
                                        status=bp.status,
                                        created_by=bp.created_by,)
        bp_created = await create_button_permission(
            db=db,
            bp= bp_data,
            created_by=bp.created_by
        )
        created_permissions["button"].append({
            "id": bp_created.id,
            "menu_id": bp_created.menu_id,
            "button_id": bp_created.button_id,
            "permission": bp_created.button_permission
        })

    action = "updated" if data.update else "created"
    return {
        "message": f"User {action} successfully",
        "subscriber_id": user_id,
        "permissions_assigned": created_permissions
    }


@router.get("/read/{user_id}", response_model=UserManageResponse)
async def read_user_with_permissions(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
    # Only admin can read full details
):
    """
    Read a user with all their menu and button permissions.
    """
    # Fetch user with relationships
    description = f"Read a user with all their menu and button permissions accessed by authenticated user: {current_user['username']} "
    action = 'Uses Management Read' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/user/read',
                        action= action, description= description, is_backend= True, input_params= user_id)
   
    result = await db.execute(
    select(User)
    .options(
        selectinload(User.role),

        selectinload(User.menu_permissions)
            .selectinload(MenuPermission.menu),

        # FIRST branch: menu
        selectinload(User.button_permissions)
            .selectinload(ButtonPermission.menu),

        # SECOND branch: button
        selectinload(User.button_permissions)
            .selectinload(ButtonPermission.button),
    )
    .where(User.id == user_id)
)

    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    # Build response
    menu_perms = [
    PermissionDetail(
        id=mp.id,
        menu_id=mp.menu_id,
        menu_name=mp.menu.menu_name if mp.menu else None,  # ✅ add this
        status=mp.status
    )
    for mp in user.menu_permissions
]

    button_perms = [
        ButtonPermissionDetail(
            id=bp.id,
            menu_id=bp.menu_id,
            button_id=bp.button_id,
            button_name=bp.button.button_name,
            button_permission=bp.button_permission,
            status=bp.status
        )
        for bp in user.button_permissions
    ]

    return UserManageResponse(
        subscriber_id=user.id,
        username=user.username,
        company= user.company_name,
        mobile= user.mobile,
        email=user.email,
        role_id=user.role_id,
        group_id=user.group_id,
        status=user.status,
        created_by= user.created_by,
        updated_by= user.updated_by,
        profile= user.profile_path,
        logo = user.company_logo,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role_name=user.role.role_name if user.role else None,
        menu_permissions=menu_perms,
        button_permissions=button_perms
    )


@router.delete("/delete/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(request: Request, 
                      user_id: int, 
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_user_permissions_detailed)):

    description = f"Delete a user with all their menu and button permissions accessed by authenticated user: {current_user['username']} "
    action = 'Uses Management Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/user/delete',
                        action= action, description= description, is_backend= True, input_params= user_id)
   
    # 1️⃣ Check if user exists
    result = await db.execute(
    select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await delete_user_with_permissions(db, user_id = user_id)

        return {"message": "User and permissions deleted successfully"}

    except Exception as e:
        # db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/profile/{user_id}")
async def update_profile(
    request: Request,
    user_id: int = Path(..., description="Subscriber ID"),
    profile_image: Optional[UploadFile] = File(None),
    company_logo: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"Update or Create the Profile and company logo endpoints accessed by authenticated user: {current_user['username']} "
    action = 'Users Profile' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/user/profile',
                        action= action, description= description, is_backend= True, input_params= user_id)

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    update_data = {}
    update_data1 = {}

    # Handle profile_image
    if profile_image and profile_image.filename:

        filename = subscriber.profile_path if subscriber.profile_path else generate_filename(profile_image.filename)
        profile_path = os.path.join(PROFILE_DIR, filename)

        # Save file
        with open(profile_path, "wb") as f:
            content = await profile_image.read()
            f.write(content)
        # if not subscriber.profile_path:
        update_data["profile_path"] = filename
        update_data1["profile_path"] = filename

    # Handle company_logo
    if company_logo and company_logo.filename:
        filename = subscriber.company_logo if subscriber.company_logo else generate_filename(company_logo.filename)
        logo_path = os.path.join(LOGO_DIR, filename)

        # Save file
        with open(logo_path, "wb") as f:
            content = await company_logo.read()
            f.write(content)
        # if not subscriber.company_logo:
        update_data["company_logo"] = filename
        update_data1["company_logo"] = filename

    # If nothing to update
    if not update_data1:
        raise HTTPException(status_code=400, detail="No files provided")
    if update_data:
        update_data['updated_by'] = user_id
        # Update database
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
        )
        await db.execute(stmt)
        await db.commit()

    return {
        "message": "Profile updated successfully",
        "updated_fields": list(update_data1.keys()),
        "user_id": user_id,
    }