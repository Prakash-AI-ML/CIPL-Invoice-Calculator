
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from app.db.session import get_db  # Make sure this yields AsyncSession
from app.crud.category import get_category, get_categories, create_category, update_category, deactivate_category, delete_category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs

# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()  # Optional: add prefix and tags

@router.post("/create", response_model=CategoryCreate)
async def create_new_category(
    request: Request,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f" Create category accessed by authenticated user: {current_user['username']} "
    action = 'Create category' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/create',
                        action= action, description= description, is_backend= True, input_params= category.model_dump())

    logger.info(
            f"CategoryCreate  accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {category or 'None'}"
        )
    # ← await the async CRUD function
    new_category = await create_category(db=db, category=category)
    return new_category


@router.get("/lists", response_model=List[CategoryResponse])
async def read_categories(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Category Lists accessed by authenticated user: {current_user['username']} "
    action = 'Category Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/lists',
                        action= action, description= description, is_backend= True, input_params= None)

    logger.info(
            f"Category Lists accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    # ← await here
    db_category = await get_categories(db=db, skip=skip, limit=limit)
    return db_category


@router.get("/list/{category_id}", response_model=CategoryResponse)
async def read_category(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Category List  for Category {category_id} accessed by authenticated user: {current_user['username']} "
    action = f'Category List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/list',
                        action= action, description= description, is_backend= True, input_params= category_id)

    logger.info(
            f"Category List accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {category_id or 'None'}"
        )
    # ← await here
    db_category = await get_category(db=db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_category


@router.put("/update/{category_id}", response_model=CategoryResponse)
async def update_existing_category(
    request: Request,
    category_id: int,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Category Update for role {category_id} accessed by authenticated user: {current_user['username']} "
    action = f'Category Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/update',
                        action= action, description= description, is_backend= True, input_params= category.model_dump())

    logger.info(
            f"Category Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {category or 'None'} for {category_id}"
        )
    # ← await here
    db_category = await update_category(db=db, category_id=category_id, category_update=category)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_category


@router.delete("/deactivate/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_route(
    request: Request,
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Category deactivate for role {category_id} accessed by authenticated user: {current_user['username']} "
    action = f'Category deactivate' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/deactivate',
                        action= action, description= description, is_backend= True, input_params= category_id)

    logger.info(
            f"Category deactivate accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {category_id or 'None'}"
        )
    # ← await here
    success = await deactivate_category(db=db, category_id=category_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return None  # 204 No Content


@router.delete("/delete/{category_id}")
async def delete_category_route(
    request: Request,
    category_id: int,
    category_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    description = f"Category Delete for role {category_name} accessed by authenticated user: {current_user['username']} "
    action = f'Category Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/category/delete',
                        action= action, description= description, is_backend= True, input_params= category_name)

    logger.info(
        f"Category Delete accessed by {current_user['username']} "
        f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
        f"at {datetime.utcnow()} | category_id={category_id}"
    )

    result = await delete_category(db=db, category_id=category_id, category_name= category_name)

    # Role not found
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Users assigned → block delete
    if not result["can_delete"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Category is assigned to clients. Reassign or delete Clients before deleting this category.",
                "clients": result["clients"],
            },
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
