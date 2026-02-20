import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_user_permissions_detailed, check_menu_permission, check_button_permission
# from app.api.deps import require_any_role  # Requires auth, no role restriction
from app.db.session import get_db
from app.schemas.approval import ApprovalRequest, UpdateApprovalRequest
from app.approval.approval_listing import get_client_data, get_client_invoices_new, get_current_payments
from app.approval.approval_crud import update_approval
from app.models.user import UserRole
from app.crud.log_manage import backend_logs
# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter( tags=["Approval Details"])

MENU_NAME = 'approval'

@router.post("/lists")
async def approval_client_lists(
    request: Request,
    data: ApprovalRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    if menu_permission and data.customer_id:
        button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
                        action= action, description= description, is_backend= True, input_params= data.model_dump())

    logger.info(
            f"Approval Listing accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {data or 'None'}"
        )
    clients = await get_client_data(
        session = session,
        customer_id = data.customer_id,
        status = data.status,
        filter = data
    )
    return {"clients": clients}



@router.post("/current-payments")
async def approval_client_lists(
    request: Request,
    data: ApprovalRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    if menu_permission and data.customer_id:
        button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
                        action= action, description= description, is_backend= True, input_params= data.model_dump())

    logger.info(
            f"Approval Listing accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {data or 'None'}"
        )
    clients = await get_current_payments(
        session = session,
        status = data.status,
        filter = data
    )
    return {"clients": clients}


@router.post("/notification")
async def approval_client_lists(
    data: ApprovalRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'notification')
    
    logger.info(
            f"Approval Listing accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {data or 'None'}"
        )
    clients = await get_client_invoices_new(
        session = session,
        customer_id = data.customer_id,
        status = data.status
    )
    return {"clients": clients}


@router.put("/update")
async def insert_client(
    request: Request,
    data: UpdateApprovalRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'approve')

    description = f"Approval status Update accessed by authenticated user: {current_user['username']} "
   
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/update',
                        action= "Approval Update", description= description, is_backend= True, input_params= data.model_dump())
    logger.info(
            f"Approval Update accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {data or 'None'}"
        )

    try:
        results = []
        for payment in data.payments:
            result = await update_approval(session= session, data = payment)
            results.append(result)

        return results
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"insert_or_update_client failed for ref_no={data}: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert client")
