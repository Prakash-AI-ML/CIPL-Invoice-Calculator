import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_user_permissions_detailed, check_button_permission, check_menu_permission
 # Requires auth, no role restriction
from app.db.session import get_db
from app.crud.log_manage import backend_logs
from app.schemas.clients import ClientInsertRequest, ClientsRequest
from app.clients.clients_listing import get_client_data
from app.clients.client_details import insert_or_update_client
# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()

MENU_NAME = 'clients'

@router.post("/lists")
async def client_lists(
    request: Request,
    data: ClientsRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    if menu_permission and data.customer_id:
        button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')
    description = f"Client Listing accessed by authenticated user: {current_user['username']} "
    action = 'Client lists' if not data.customer_id else f'Client list for client {data.customer_id}'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client/lists',
                        action= action, description= description, is_backend= True, input_params= data.model_dump())

    logger.info(
            f"Client Listing accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {filter or 'None'}"
        )
    clients = await get_client_data(
        session = session,
        customer_id = data.customer_id,
        status = data.status
    )
    # if clients:
    return {"clients": clients}
   

@router.put("/insert")
async def insert_client(
    request: Request,
    data: ClientInsertRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    description = f"Client Category and payment term insert endpoint accessed by authenticated user: {current_user['username']} "
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client/lists',
                        action= 'Client Insert', description= description, is_backend= True, input_params= data.model_dump())

    logger.info(
            f"Client Insert accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} | data: {filter or 'None'}"
        )
    data = data.model_dump(exclude_none=True) 
    try:
        result = await insert_or_update_client(session= session, **data)

        return result
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"insert_or_update_client failed for ref_no={data}: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert client")
