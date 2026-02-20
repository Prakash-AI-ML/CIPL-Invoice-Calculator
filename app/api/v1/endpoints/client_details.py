
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_user_permissions_detailed, check_button_permission, check_menu_permission
 # Requires auth, no role restriction
from app.db.session import get_db
from app.schemas.client_details import ClientCreate, ClientUpdate
from app.crud.client_details import get_clients, get_clients_edit, insert_client, update_client, delete_client
from app.crud.log_manage import backend_logs

import logging
from datetime import datetime
# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/read")
async def get_clients__(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')
    description = f"Client-Detail Lists accessed by authenticated user: {current_user['username']} "
    action = 'Client-Detail Lists' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client-details/read',
                        action= action, description= description, is_backend= True, input_params= None)

    logger.info(
            f"Client-Detail Lists accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    clients = await get_clients(
        session = session
    )
    return {"clients": clients}


@router.get("/read/{client_index}")
async def get_clients___(
    request: Request,
    client_index: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')
    description = f"Client-Detail List  for client-detail {client_index} accessed by authenticated user: {current_user['username']} "
    action = f'Client-Detail List' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client-details/read',
                        action= action, description= description, is_backend= True, input_params= client_index)

    logger.info(
            f"Client-Detail list accessed by authenticated user: {current_user['username']} "
            f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
            f"at {datetime.utcnow()} "
        )
    clients = await get_clients_edit(
        session = session,
        client_index= client_index
    )
    return {"clients": clients}


@router.post("/create")
async def create_client(
    request: Request,
    client: ClientCreate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    client = client.model_dump()
    description = f" Create Client-Detail accessed by authenticated user: {current_user['username']} "
    action = 'Create Client-Detail' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client-details/create',
                        action= action, description= description, is_backend= True, input_params= client)

    
    client_id = await insert_client(session, client)
    return {"id": client_id}


@router.put("/update/{client_id}")
async def edit_client(
    request: Request,
    client_id: int,
    client: ClientUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    client = client.model_dump()
    description = f"Client-Detail Update for client-details {client_id} accessed by authenticated user: {current_user['username']} "
    action = f'Client-Detail Update' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client-details/update',
                        action= action, description= description, is_backend= True, input_params= client)

    updated = await update_client(session, client_id, client)
    if updated == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client updated"}



@router.delete("/delete/{client_index}")
async def remove_client(
    request: Request,
    client_index: int,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    description = f"Client-Detail Delete for role {client_index} accessed by authenticated user: {current_user['username']} "
    action = f'Client-Detail Delete' 
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/client-details/delete',
                        action= action, description= description, is_backend= True, input_params= client_index)

    deleted = await delete_client(session, client_index)

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Client not found")

    return {"message": "Client deleted successfully"}
