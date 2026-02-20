
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from app.db.session import get_db  # Make sure this yields AsyncSession
from app.crud.role import create_role, get_role, get_roles, update_role, delete_role, deactivate_role
from app.schemas.roles import RoleCreate, RoleUpdate, RoleResponse
from app.crud.log_manage import backend_logs
from app.api.dependencies import get_user_permissions_detailed

# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()  # Optional: add prefix and tags

@router.post("/create", response_model=RoleResponse)
async def create_new_role(
    request: Request,
    role: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create role accessed by authenticated user: {current_user['username']} "
    action = 'Create role' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/create',
                        action= action, description= description, is_backend= True, input_params= role.model_dump())

    logger.info(
            f"RoleCreate  accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {role or 'None'}"
        )
    # ← await the async CRUD function
    new_role = await create_role(db=db, role=role)
    return new_role


@router.get("/lists", response_model=List[RoleResponse])
async def read_roles(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Role Lists accessed by authenticated user: {current_user['username']} "
    action = 'Role Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/lists',
                        action= action, description= description, is_backend= True, input_params= None)

    logger.info(
            f"Role Lists accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    # ← await here
    roles = await get_roles(db=db, skip=skip, limit=limit)
    return roles


@router.get("/list/{role_id}", response_model=RoleResponse)
async def read_role(
    request: Request,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Role List  for role {role_id} accessed by authenticated user: {current_user['username']} "
    action = f'Role List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/list',
                        action= action, description= description, is_backend= True, input_params= role_id)

    logger.info(
            f"Role List accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {role_id or 'None'}"
        )
    # ← await here
    db_role = await get_role(db=db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role


@router.put("/update/{role_id}", response_model=RoleResponse)
async def update_existing_role(
    request: Request,
    role_id: int,
    role: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Role Update for role {role_id} accessed by authenticated user: {current_user['username']} "
    action = f'Role Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/update',
                        action= action, description= description, is_backend= True, input_params= role.model_dump())

    logger.info(
            f"Role Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {role or 'None'} for {role_id}"
        )
    # ← await here
    db_role = await update_role(db=db, role_id=role_id, role_update=role)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role


@router.delete("/deactivate/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role_route(
    request: Request,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Role deactivate for role {role_id} accessed by authenticated user: {current_user['username']} "
    action = f'Role deactivate' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/deactivate',
                        action= action, description= description, is_backend= True, input_params= role_id)

    logger.info(
            f"Role deactivate accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {role_id or 'None'}"
        )
    # ← await here
    success = await deactivate_role(db=db, role_id=role_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return None  # 204 No Content

@router.delete("/delete/{role_id}")
async def delete_role_route(
    request: Request,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    description = f"Role Delete for role {role_id} accessed by authenticated user: {current_user['username']} "
    action = f'Role Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/roles/delete',
                        action= action, description= description, is_backend= True, input_params= role_id)

    logger.info(
        f"Role Delete accessed by {current_user['username']} "
        f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
        f"at {datetime.utcnow()} | role_id={role_id}"
    )

    result = await delete_role(db=db, role_id=role_id)

    # Role not found
    if result is None:
        raise HTTPException(status_code=404, detail="Role not found")

    # Users assigned → block delete
    if not result["can_delete"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Role is assigned to users. Reassign or delete users before deleting this role.",
                "users": result["users"],
            },
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
