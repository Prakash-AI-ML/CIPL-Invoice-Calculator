
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from app.db.session import get_db
from app.crud.button_permissions import (
    create_button_permission,
    get_button_permission,
    get_button_permissions_by_user_menu,  # Updated: user + menu based
    update_button_permission,
    delete_button_permission
)
from app.schemas.buttons import (
    ButtonPermissionCreate,
    ButtonPermissionUpdate,
    ButtonPermissionResponse
)
from app.crud.log_manage import backend_logs
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=ButtonPermissionResponse)
async def create_new_bp(
    request: Request,
    bp: ButtonPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create ButtonPermission accessed by authenticated user: {current_user['username']} "
    action = 'Create ButtonPermission' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/create',
                        action= action, description= description, is_backend= True, input_params= bp.model_dump())
    logger.info(
            f"ButtonPermission Create accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {bp or 'None'}"
        )
    
    new_bp = await create_button_permission(db=db, bp=bp, created_by=current_user['user_id'])
    return new_bp


@router.get("/list/{bp_id}", response_model=ButtonPermissionResponse)
async def read_bp(
    request: Request,
    bp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"ButtonPermission List  for ButtonPermission {bp_id} accessed by authenticated user: {current_user['username']} "
    action = f'ButtonPermission List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/list',
                        action= action, description= description, is_backend= True, input_params= bp_id)

    logger.info(
            f"ButtonPermission list accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {bp_id or 'None'}"
        )
    db_bp = await get_button_permission(db=db, bp_id=bp_id)
    if db_bp is None:
        raise HTTPException(status_code=404, detail="Button Permission not found")
    return db_bp


# New endpoint: Get all button permissions for current user + specific menu
@router.get("/list/{menu_id}", response_model=List[ButtonPermissionResponse])
async def read_bps_for_current_user_menu(
    request: Request,
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"ButtonPermission List  for Menu {menu_id} accessed by authenticated user: {current_user['username']} "
    action = f'ButtonPermission List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/list',
                        action= action, description= description, is_backend= True, input_params= menu_id)

    logger.info(
            f"ButtonPermission list accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu_id or 'None'}"
        )
    
    bps = await get_button_permissions_by_user_menu(
        db=db,
        user_id=current_user['user_id'],
        menu_id=menu_id
    )
    return bps


@router.put("/update/{bp_id}", response_model=ButtonPermissionResponse)
async def update_bp(
    request: Request,
    bp_id: int,
    bp: ButtonPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"ButtonPermission Update for ButtonPermission {bp_id} accessed by authenticated user: {current_user['username']} "
    action = f'ButtonPermission Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/update',
                        action= action, description= description, is_backend= True, input_params= bp.model_dump())

    logger.info(
            f"ButtonPermission update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {bp or 'None'} for {bp_id}"
        )
    updated_bp = await update_button_permission(
        db=db,
        bp_id=bp_id,
        bp_update=bp,
        updated_by=current_user['user_id']
    )
    if updated_bp is None:
        raise HTTPException(status_code=404, detail="Button Permission not found")
    return updated_bp


@router.delete("/delete/{bp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bp(
    request: Request,
    bp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"ButtonPermission Delete for ButtonPermission {bp_id} accessed by authenticated user: {current_user['username']} "
    action = f'ButtonPermission Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/delete',
                        action= action, description= description, is_backend= True, input_params= bp_id)

    logger.info(
            f"ButtonPermission delete accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {bp_id or 'None'}"
        )
    success = await delete_button_permission(db=db, bp_id=bp_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Button Permission not found")
    return None