from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from app.db.session import get_db  # Must yield AsyncSession
from app.crud.menus import create_menu, get_menu, get_menus, update_menu, delete_menu, deactivate_menu
from app.schemas.menus import MenuCreate, MenuUpdate, MenuResponse
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs

# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=MenuResponse)
async def create_new_menu(
    request: Request,
    menu: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create Menu accessed by authenticated user: {current_user['username']} "
    action = 'Create Menu' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/create',
                        action= action, description= description, is_backend= True, input_params= menu.model_dump())

    logger.info(
            f"Menu Create accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu or 'None'}"
        )
    new_menu = await create_menu(db=db, menu=menu, created_by=current_user['user_id'])
    return new_menu


@router.get("/lists", response_model=List[MenuResponse])
async def read_menus(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Menu Lists accessed by authenticated user: {current_user['username']} "
    action = 'Menu Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/lists',
                        action= action, description= description, is_backend= True, input_params= None)

    logger.info(
            f"Menu Lists accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    menus = await get_menus(db=db, skip=skip, limit=limit)
    return menus


@router.get("/list/{menu_id}", response_model=MenuResponse)
async def read_menu(
    request: Request,
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Menu List  for Menu {menu_id} accessed by authenticated user: {current_user['username']} "
    action = f'Menu List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/list',
                        action= action, description= description, is_backend= True, input_params= menu_id)

    logger.info(
            f"Menu List accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu_id or 'None'}"
        )
    db_menu = await get_menu(db=db, menu_id=menu_id)
    if db_menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Optional: Permission check using user-specific menu_permissions
    # Since permissions are now per-user (subscribers_id), you can check:
    user_menu_ids = [mp.menu_id for mp in current_user.menu_permissions]
    if menu_id not in user_menu_ids:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return db_menu


@router.put("/update/{menu_id}", response_model=MenuResponse)
async def update_existing_menu(
    request: Request,
    menu_id: int,
    menu: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Menu Update for Menu {menu_id} accessed by authenticated user: {current_user['username']} "
    action = f'Menu Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/update',
                        action= action, description= description, is_backend= True, input_params= menu.model_dump())

    logger.info(
            f"Menu Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu_id or 'None'}"
        )
    updated_menu = await update_menu(
        db=db,
        menu_id=menu_id,
        menu_update=menu,
        updated_by=current_user['user_id']
    )
    if updated_menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return updated_menu


@router.delete("/deactivate/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_route(
    request: Request,
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Menu deactivate for Menu {menu_id} accessed by authenticated user: {current_user['username']} "
    action = f'Menu deactivate' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/deactivate',
                        action= action, description= description, is_backend= True, input_params= menu_id)

    logger.info(
            f"Menu deactivate accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu_id or 'None'}"
        )
    success = await deactivate_menu(db=db, menu_id=menu_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Menu not found")
    return None  # 204 No Content

@router.delete("/delete/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_route(
    request: Request,
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Menu Delete for Menu {menu_id} accessed by authenticated user: {current_user['username']} "
    action = f'Menu Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/menus/delete',
                        action= action, description= description, is_backend= True, input_params= menu_id)

    logger.info(
            f"Menu delete accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {menu_id or 'None'}"
        )
    success = await delete_menu(db=db, menu_id=menu_id)
    if not success:
        raise HTTPException(status_code=404, detail="Menu not found")
    return None  # 204 No Content