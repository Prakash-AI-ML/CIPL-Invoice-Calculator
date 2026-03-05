from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
    UploadFile,
    File, Form
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.crud.delivery_order_settings import (
    create_delivery_order,
    get_delivery_orders,
    get_delivery_order,
    update_delivery_order,
    deactivate_delivery_order,
    delete_delivery_order,
)
from app.schemas.delivery_order_settings import (
    DeliveryOrderCreate,
    DeliveryOrderUpdate,
    DeliveryOrderResponse,
)
import uuid
import os
from app.models.user import User  # your user model
from app.api.dependencies import get_user_permissions_detailed
from pathlib import Path

router = APIRouter()


@router.post("/create", response_model=DeliveryOrderResponse, status_code=201)
async def create_delivery_order_settings(
    company_name: str = Form(...),
    address: str = Form(...),
    status: int = Form(1),
    company_logo: Optional[UploadFile] = File(None),   # optional file
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Create Delivery Order Settings using form-data
    All fields + optional logo file are sent as multipart/form-data
    """
    # Optional: you can add permission/ownership check here
    # e.g. if current_user['user_id'] != created_by: raise 403

    # Prepare schema-like dict (since we're not using Pydantic model directly)
    create_data = {
        "company_name": company_name,
        "address": address,
        "status": status,
        "created_by": current_user['user_id'],
        "updated_by": current_user['user_id'],
    }
    

    logo_url = None

    if company_logo and company_logo.filename:
        # Generate unique filename
        original_ext = Path(company_logo.filename).suffix.lower() or ".png"
        unique_name = f"{uuid.uuid4().hex}{original_ext}"
        file_path =  unique_name
        file_path = os.path.join(r"app/static/app/assets/do/", unique_name)

        # Save file
        content = await company_logo.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)


    # Add logo URL if uploaded
    
    create_data["company_logo"] = unique_name

    data=DeliveryOrderCreate(**create_data)
    

    # Use your existing CRUD function (adapted to take dict + logo handling already done)
    new_item = await create_delivery_order(
        db=db,
        data=DeliveryOrderCreate(**create_data),  # or modify CRUD to accept dict
        logo_file=None,                           # we already handled file
        created_by=current_user['user_id'],
    )

    return new_item

@router.get("/read", response_model=List[DeliveryOrderResponse])
async def list_delivery_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    client_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    items = await get_delivery_orders(db, skip, limit, client_id)
    return items


@router.get("/read/{do_id}", response_model=DeliveryOrderResponse)
async def get_one_do(
    do_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    print(do_id)
    obj = await get_delivery_order(db, do_id)
    if not obj:
        raise HTTPException(404, "Delivery order settings not found")
    return obj


@router.patch("/update{do_id}", response_model=DeliveryOrderResponse)
async def update_do(
    data: DeliveryOrderUpdate,
    do_id: int = 1,
    company_logo: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    obj = await update_delivery_order(
        db=db,
        do_id=do_id,
        update_data=data,
        logo_file=company_logo,
    )
    if not obj:
        raise HTTPException(404, "Not found")
    return obj


@router.delete("/delete/{do_id}", status_code=204)
async def delete_do(
    do_id: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    success = await delete_delivery_order(db, do_id)
    if not success:
        raise HTTPException(404, "Not found")
    return None


@router.post("/{do_id}/deactivate", status_code=200)
async def deactivate_do(
    do_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    success = await deactivate_delivery_order(db, do_id, updated_by=current_user['user_id'])
    if not success:
        raise HTTPException(404, "Not found")
    return {"message": "Deactivated successfully"}