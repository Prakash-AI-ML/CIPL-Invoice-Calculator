
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db  # Must yield AsyncSession
from app.crud.user import (
    create_user,
    get_user,
    get_users,
    update_user,
    delete_user,
    get_user_by_email, deactivate_user
)
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserReadResponse, RoleRead
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs

router = APIRouter()

@router.post("/create", response_model=UserResponse)
async def create_new_user(
    request: Request,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f" Create Users accessed by authenticated user: {current_user['username']} "
    action = 'Create Users' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/create',
                        action= action, description= description, is_backend= True, input_params= user.model_dump())

    # Check if email exists — await async function
    db_user = await get_user_by_email(db=db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = await create_user(db=db, user=user, created_by=current_user['user_id'])
    return new_user


@router.get("/read")
async def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"Users Lists accessed by authenticated user: {current_user['username']} "
    action = 'Users Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/read',
                        action= action, description= description, is_backend= True, input_params= None)

    users = await get_users(db=db, skip=skip, limit=limit)
    return users


@router.get("/read/{user_id}")
async def read_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"User List  for user {user_id} accessed by authenticated user: {current_user['username']} "
    action = f'User List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/read',
                        action= action, description= description, is_backend= True, input_params= user_id)

    db_user = await get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserReadResponse(
    id=db_user.id,
    company= db_user.company_name,
    mobile= db_user.mobile,
    username=db_user.username,
    email=db_user.email,
    role_id=db_user.role_id,
    group_id=db_user.group_id,
    status=db_user.status,
    profile= db_user.profile_path,
    logo = db_user.company_logo,
    created_by= db_user.created_by,
    updated_by=db_user.updated_by,
    role=RoleRead(
        role_id=db_user.role.id,
        role_name=db_user.role.role_name,
        status=db_user.role.status
    ) if db_user.role else None
)


@router.put("/update/{user_id}", response_model=UserResponse)
async def update_existing_user(
    request: Request,
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"Users Update for Users {user_id} accessed by authenticated user: {current_user['username']} "
    action = f'Users Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/update',
                        action= action, description= description, is_backend= True, input_params= user.model_dump())

    db_user = await update_user(db=db, user_id=user_id, user_update=user, updated_by=current_user['user_id'])
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/deactivate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"Users deactivate for Users {user_id} accessed by authenticated user: {current_user['username']} "
    action = f'Users deactivate' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/deactivate',
                        action= action, description= description, is_backend= True, input_params= user_id)

    success = await deactivate_user(db=db, user_id=user_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None  # 204 No Content

@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed)
):
    description = f"Users Delete for Users {user_id} accessed by authenticated user: {current_user['username']} "
    action = f'Users Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/users/delete',
                        action= action, description= description, is_backend= True, input_params= user_id)

    success = await delete_user(db=db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None  # 204 No Content