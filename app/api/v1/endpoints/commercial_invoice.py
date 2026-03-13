# app/api/v1/routers/commercial_invoice.py
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Path,
)
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.crud.commercial_invoice import (
    create_commercial_invoice,
    get_commercial_invoices,
    get_commercial_invoice,
    get_commercial_invoice_by_reference,
    update_commercial_invoice,
    deactivate_commercial_invoice,
    delete_commercial_invoice,
)
from app.schemas.commercial_invoice import (
    CommercialInvoiceCreate,
    CommercialInvoiceUpdate,
    CommercialInvoiceOut,
)
from app.models.user import User
from app.api.dependencies import get_user_permissions_detailed

router = APIRouter(
)


@router.post(
    "/create",
    response_model=CommercialInvoiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new commercial invoice record"
)
async def create_invoice(
    invoice_in: CommercialInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Create a new commercial invoice entry with full JSON data.
    """
    try:
        new_invoice = await create_commercial_invoice(
            db=db,
            data=invoice_in,
            created_by=current_user["user_id"]
        )
        return new_invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/read",
    response_model=List[CommercialInvoiceOut],
    summary="List commercial invoices with pagination and filters"
)
async def list_invoices(
    skip: int = Query(0, ge=0, description="Records to skip (offset)"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    reference_number: Optional[str] = Query(None, description="Filter by reference number (partial match)"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE/INACTIVE)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Get list of commercial invoices (paginated).
    """
    items = await get_commercial_invoices(
        db=db,
        skip=skip,
        limit=limit,
        reference_number=reference_number,
        status=status,
    )
    return items


@router.get(
    "/read/{invoice_id}",
    response_model=CommercialInvoiceOut,
    summary="Get a single commercial invoice by ID"
)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Retrieve one commercial invoice by its internal ID.
    """
    invoice = await get_commercial_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Commercial invoice not found")
    return invoice


@router.get(
    "/read/by-reference/{reference_number}",
    response_model=CommercialInvoiceOut,
    summary="Get commercial invoice by reference number"
)
async def get_invoice_by_reference(
    reference_number: str = Path(..., min_length=1, max_length=80),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Retrieve invoice using the business reference number (e.g. ES-00130).
    """
    invoice = await get_commercial_invoice_by_reference(db, reference_number)
    if not invoice:
        raise HTTPException(status_code=404, detail="Commercial invoice not found")
    return invoice


@router.patch(
    "/update/{reference_number}",
    response_model=CommercialInvoiceOut,
    summary="Update an existing commercial invoice"
)
async def update_invoice(
    reference_number: str,
    invoice_update: CommercialInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Partially update a commercial invoice (including JSON data if provided).
    """
    updated_invoice = await update_commercial_invoice(
        db=db,
        reference_number=reference_number,
        update_data=invoice_update,
        updated_by=current_user["user_id"]
    )
    if not updated_invoice:
        raise HTTPException(status_code=404, detail=f"Commercial invoice not found\n {updated_invoice}")
    return updated_invoice


@router.delete(
    "/delete/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a commercial invoice"
)
async def delete_invoice(
    invoice_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Hard delete of the invoice record.
    """
    success = await delete_commercial_invoice(db, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Commercial invoice not found")
    return None


@router.post(
    "/{invoice_id}/deactivate",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Soft deactivate (set status to INACTIVE)"
)
async def deactivate_invoice(
    invoice_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_user_permissions_detailed),
):
    """
    Mark the invoice as inactive instead of deleting it.
    """
    success = await deactivate_commercial_invoice(
        db=db,
        invoice_id=invoice_id,
        updated_by=current_user["user_id"]
    )
    if not success:
        raise HTTPException(status_code=404, detail="Commercial invoice not found")

    return {"message": "Commercial invoice deactivated successfully"}