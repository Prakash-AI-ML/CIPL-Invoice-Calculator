from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path
)

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.crud.cipl_desc import (
    create_cipl_desc,
    get_cipl_descs,
    get_cipl_desc,
    update_cipl_desc,
    deactivate_cipl_desc,
    delete_cipl_desc,
)

from app.schemas.cipl_desc import (
    CiplDescCreate,
    CiplDescUpdate,
    CiplDescOut,
)
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed

router = APIRouter()


@router.post("/create", response_model=CiplDescOut, status_code=201)
async def create_cipl_description(
    data: CiplDescCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    new_item = await create_cipl_desc(
        db=db,
        data=data,
        created_by=current_user["user_id"]
    )

    return new_item



@router.get("/read", response_model=List[CiplDescOut])
async def list_cipl_desc(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    item_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    items = await get_cipl_descs(db, skip, limit, item_id)
    return items

@router.get("/read/{desc_id}", response_model=CiplDescOut)
async def get_one_cipl_desc(
    desc_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    obj = await get_cipl_desc(db, desc_id)

    if not obj:
        raise HTTPException(404, "CIPL description not found")

    return obj


@router.patch("/update/{desc_id}", response_model=CiplDescOut)
async def update_cipl_description(
    desc_id: int,
    data: CiplDescUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    obj = await update_cipl_desc(
        db=db,
        desc_id=desc_id,
        update_data=data,
        updated_by=current_user["user_id"]
    )

    if not obj:
        raise HTTPException(404, "CIPL description not found")

    return obj


@router.delete("/delete/{desc_id}", status_code=204)
async def delete_cipl_description(
    desc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    success = await delete_cipl_desc(db, desc_id)

    if not success:
        raise HTTPException(404, "CIPL description not found")

    return None

@router.post("/{desc_id}/deactivate", status_code=200)
async def deactivate_cipl_description(
    desc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    success = await deactivate_cipl_desc(
        db,
        desc_id,
        updated_by=current_user["user_id"]
    )

    if not success:
        raise HTTPException(404, "CIPL description not found")

    return {"message": "Deactivated successfully"}



