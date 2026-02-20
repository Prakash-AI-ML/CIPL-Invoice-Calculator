
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import logging

from app.db.session import get_db  # Yields AsyncSession
from app.crud.buttons import (
    create_button,
    get_button,
    get_buttons,
    update_button,
    delete_button, deactivate_button
)
from app.crud.log_manage import backend_logs
from app.schemas.buttons import ButtonCreate, ButtonUpdate, ButtonResponse
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=ButtonResponse)
async def create_new_button(
    request: Request,
    button: ButtonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create Button accessed by authenticated user: {current_user['username']} "
    action = 'Create Button' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/create',
                        action= action, description= description, is_backend= True, input_params= button.model_dump())
    logger.info(
            f"ButtonCreate  accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {button or 'None'}"
        )
    
    new_button = await create_button(db=db, button=button, created_by=current_user['user_id'])
    return new_button


@router.get("/lists", response_model=List[ButtonResponse])
async def read_buttons(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Button Lists accessed by authenticated user: {current_user['username']} "
    action = 'Button Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/lists',
                        action= action, description= description, is_backend= True, input_params= None)
    logger.info(
            f"Button Lists  accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    buttons = await get_buttons(db=db, skip=skip, limit=limit)
    return buttons


@router.get("/list/{button_id}", response_model=ButtonResponse)
async def read_button(
    request: Request,
    button_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Button List  for Button {button_id} accessed by authenticated user: {current_user['username']} "
    action = f'Button List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/list',
                        action= action, description= description, is_backend= True, input_params= button_id)

    logger.info(
            f"Button list  accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {button_id or 'None'}"
        )
    db_button = await get_button(db=db, button_id=button_id)
    if db_button is None:
        raise HTTPException(status_code=404, detail="Button not found")

    # Note: Full button permission check usually happens in the context of a menu
    # (e.g., when loading buttons for a specific menu)
    # You can add a check here if needed, using current_user.button_permissions
    # Example:
    # user_button_ids = [bp.button_id for bp in current_user.button_permissions]
    # if button_id not in user_button_ids:
    #     raise HTTPException(status_code=403, detail="Insufficient permissions")

    return db_button


@router.put("/update/{button_id}", response_model=ButtonResponse)
async def update_existing_button(
    request: Request,
    button_id: int,
    button: ButtonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Button Update for Button {button_id} accessed by authenticated user: {current_user['username']} "
    action = f'Button Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/update',
                        action= action, description= description, is_backend= True, input_params= button.model_dump())

    logger.info(
            f"Button Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {button or 'None'} |  button_id: {button_id or 'None'}"
        )
    updated_button = await update_button(
        db=db,
        button_id=button_id,
        button_update=button,
        updated_by=current_user['user_id']
    )
    if updated_button is None:
        raise HTTPException(status_code=404, detail="Button not found")
    return updated_button


@router.delete("/deactivate/{button_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_button_route(
    request: Request,
    button_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Button deactivate for Button {button_id} accessed by authenticated user: {current_user['username']} "
    action = f'Button deactivate' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/deactivate',
                        action= action, description= description, is_backend= True, input_params= button_id)

    logger.info(
            f"Button deactivate accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {button_id or 'None'}"
        )
    success = await deactivate_button(db=db, button_id=button_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Button not found")
    return None  # 204 No Content


@router.delete("/delete/{button_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_button_route(
    request: Request,
    button_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"RoButtonle Delete for Button {button_id} accessed by authenticated user: {current_user['username']} "
    action = f'Button Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/buttons/delete',
                        action= action, description= description, is_backend= True, input_params= button_id)

    logger.info(
            f"Button Delete accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {button_id or 'None'}"
        )
    success = await delete_button(db=db, button_id=button_id)
    if not success:
        raise HTTPException(status_code=404, detail="Button not found")
    return None  # 204 No Content