import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_user_permissions_detailed, check_menu_permission, check_button_permission
from app.schemas.dashboard import CashFlowRequest, CashFlowFilter
from app.db.session import get_db
from app.crud.dashboard import total_payable, get_cash_flow, cash_flow_category_monthly, total_expenses_by_category, payable_analysis, monthly_invoice_analysis, current_month_payment_analysis


from app.crud.log_manage import backend_logs
# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter( tags=["Dashboard"])

# MENU_NAME = 'approval'

@router.post("/total-payable")
async def total_payable_lists(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await total_payable(
        session = session
    )
    return {"response": responses}


@router.post("/cash-flow")
async def cash_flow(
    data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await get_cash_flow(
        session = session,
        year = data.year,
        quarter = data.quarter
    )
    return {"response": responses}


@router.post("/cash-flow-category")
async def cash_flow(
    data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await cash_flow_category_monthly(
        session = session,
        year= data.year,
        quarter= data.quarter
    )
    return {"response": responses}


@router.post("/category-expenses")
async def cash_flow(
    data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await total_expenses_by_category(
        session = session,
        year= data.year,
        quarter= data.quarter
    )
    return {"response": responses}



@router.post("/payable-analysis")
async def cash_flow(
    data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await payable_analysis(
        session = session,
        year= data.year,
        quarter= data.quarter
    )
    return {"response": responses}


@router.post("/payable-monthly")
async def cash_flow(
    data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await monthly_invoice_analysis(
        session = session,
        year= data.year,
        quarter= data.quarter
    )
    return {"response": responses}


@router.post("/current-payable")
async def current_month_payable(
    # data: CashFlowFilter,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed)
):
    # menu_permission = check_menu_permission(current_user=current_user, menu_name= MENU_NAME)
    # if menu_permission and data.customer_id:
    #     button_permission = check_button_permission(current_user=current_user, menu_name= MENU_NAME, required_button= 'view')

    # description = f"Approval Listing accessed by authenticated user: {current_user['username']} "
    # action = 'approval lists' if not data.customer_id else f'approval list for client {data.customer_id}'
    # await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/approval/lists',
    #                     action= action, description= description, is_backend= True, input_params= data.model_dump())

    # logger.info(
    #         f"Approval Listing accessed by authenticated user: {current_user['username']} "
    #         f"(email: {current_user.get('email', 'N/A')}, role: {current_user['role']}) "
    #         f"at {datetime.utcnow()} | data: {data or 'None'}"
    #     )
    responses = await current_month_payment_analysis(
        session = session,
       
    )
    return {"response": responses}