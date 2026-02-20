from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from app.db.session import get_db
from app.crud.menu_permissions import (
    create_menu_permission,
    get_menu_permission,
    get_menu_permissions_by_user,  # New: for current user
    update_menu_permission,
    delete_menu_permission
)
from app.schemas.menus import (
    MenuPermissionCreate,
    MenuPermissionUpdate,
    MenuPermissionResponse
)
from app.crud.log_manage import backend_logs
from app.api.dependencies import get_user_permissions_detailed

logger = logging.getLogger(__name__)

router = APIRouter( tags=["menu_permissions"])

@router.post("/create", response_model=MenuPermissionResponse)
async def create_new_mp(
    request: Request,
    mp: MenuPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create MenuPermission accessed by authenticated user: {current_user['username']} "
    action = 'Create MenuPermission' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menu-permissions/create',
                        action= action, description= description, is_backend= True, input_params= mp.model_dump())

    logger.info(
            f"MenuPermission Create accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {mp or 'None'}"
        )
    new_mp = await create_menu_permission(db=db, mp=mp, created_by=current_user['user_id'])
    return new_mp


# New useful endpoint: Get all menu permissions for the current user
@router.get("/list/my")
async def read_my_menu_permissions(
    request: Request,
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"MenuPermission List/MY accessed by authenticated user: {current_user['username']} "
    action = 'MenuPermission List/MY' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menu-permissions/list/my',
                        action= action, description= description, is_backend= True, input_params= None)

    logger.info(
            f"MenuPermission List/MY accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()}"
        )
    
    # mps = await get_menu_permissions_by_user(db=db, user_id=current_user.get('user_id'))
    return current_user.get('menus', {})


@router.get("/list/{mp_id}", response_model=MenuPermissionResponse)
async def read_mp(
    request: Request,
    mp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"MenuPermission List  for MenuPermission {mp_id} accessed by authenticated user: {current_user['username']} "
    action = f'MenuPermission List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menu-permissions/list',
                        action= action, description= description, is_backend= True, input_params= mp_id)

    logger.info(
            f"MenuPermission List accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {mp_id or 'None'}"
        )
    db_mp = await get_menu_permission(db=db, mp_id=mp_id)
    if db_mp is None:
        raise HTTPException(status_code=404, detail="Menu Permission not found")
    return db_mp



@router.put("/update/{mp_id}", response_model=MenuPermissionResponse)
async def update_mp(
    request: Request,
    mp_id: int,
    mp: MenuPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"MenuPermission Update for MenuPermission {mp_id} accessed by authenticated user: {current_user['username']} "
    action = f'MenuPermission Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menu-permissions/update',
                        action= action, description= description, is_backend= True, input_params= mp.model_dump())

    logger.info(
            f"MenuPermission Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {mp or 'None'} for {mp_id}"
        )
    updated_mp = await update_menu_permission(
        db=db,
        mp_id=mp_id,
        mp_update=mp,
        updated_by=current_user['user_id']
    )
    if updated_mp is None:
        raise HTTPException(status_code=404, detail="Menu Permission not found")
    return updated_mp


@router.delete("/delete/{mp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mp(
    request: Request,
    mp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"MenuPermission Delete for MenuPermission {mp_id} accessed by authenticated user: {current_user['username']} "
    action = f'MenuPermission Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menu-permissions/delete',
                        action= action, description= description, is_backend= True, input_params= mp_id)

    logger.info(
            f"MenuPermission Delete accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {mp_id or 'None'}"
        )
    success = await delete_menu_permission(db=db, mp_id=mp_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Menu Permission not found")
    return None