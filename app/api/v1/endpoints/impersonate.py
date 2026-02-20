
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import json
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.security import settings, create_access_token
from app.api.dependencies import get_user_permissions_detailed
from app.models.user import User
from app.models.roles import Role
from app.schemas.impersonate import SubscriberListResponse, SubscriberResponse
from app.crud.log_manage import backend_logs

# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter() 

@router.get("/subscribers", response_model=SubscriberResponse)
async def list_subscribers(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    # # 🔐 Backend safety check (DO NOT rely only on frontend)
    if not current_user.get("can_impersonate") and not current_user.get("impersonated"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    description = f"Impersonate Listing accessed by authenticated user: {current_user['username']} "
    action = 'Impersonate lists'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/impersonate/subscribers',
                        action= action, description= description, is_backend= True, input_params= None)

    result = await db.execute(
    select(User)
    .options(selectinload(User.role))
    .where(User.status == 1)
    .order_by(User.username)
)

    users = result.scalars().all()

    return SubscriberResponse(
    current_user_mail=current_user['email'],
    impersonated_by = current_user['impersonated_by'],
    subscribers=[
        SubscriberListResponse(
            id=user.id,
            name=user.username,
            email=user.email,
            profile_path=user.profile_path,
            role = user.role.role_name
        )
        for user in users
    ]
)

@router.post("/login/subscriber/{subscriber_id}")
async def login_as_subscriber(
    subscriber_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    # 🔐 HARD permission check
    print(current_user.get("can_impersonate"), current_user.get("impersonated"))
    if not current_user.get("can_impersonate") and not current_user.get("impersonated"):

        raise HTTPException(status_code=403, detail="Permission denied")

    # 1️⃣ Load subscriber
    result = await db.execute(
        select(User).where(User.id == subscriber_id, User.status == 1)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    # 2️⃣ Create token (mark impersonation)
    token = create_access_token({
        "sub": subscriber.email,
        "impersonated": True,
        "impersonated_by": current_user['impersonated_by'] if current_user['impersonated_by'] else current_user["user_id"],
    })

    fake_credentials = HTTPAuthorizationCredentials(
        scheme="bearer",
        credentials=token
    )

    # 3️⃣ Load permissions as subscriber
    permissions = await get_user_permissions_detailed(
        credentials=fake_credentials,
        db=db
    )

    # 4️⃣ Set cookies (same as normal login)
    # response = RedirectResponse(
    #     url=f"{settings.root_path}/app/dashboard",
    #     status_code=302
    # )
    response = JSONResponse(content={
        "success": True,
        "message": f"IMPERSONATION: {current_user['username']} logged in as subscriber_id={subscriber_id}",
        "redirect_to": f"{settings.root_path}/app/dashboard",  # optional: tell frontend where to go
        "user_id": permissions["user_id"],
        "role": permissions["role"],
    })

    response.set_cookie("access_token", token, httponly=False, path=settings.root_path or "/")
    response.set_cookie("root_path", settings.root_path, httponly=False)
    response.set_cookie("user_id", permissions["user_id"], httponly=False, secure=True, samesite="lax")
    response.set_cookie("role", permissions["role"], httponly=False, secure=True, samesite="lax")

    description = f"IMPERSONATION: {current_user['username']} logged in as subscriber_id={subscriber_id}"
    action = 'IMPERSONATION'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/impersonate/login/subscriber',
                        action= action, description= description, is_backend= True, input_params= subscriber_id)
    
    # 5️⃣ Audit log (IMPORTANT)
    logger.warning(
        f"IMPERSONATION: {current_user['username']} "
        f"logged in as subscriber_id={subscriber_id}"
    )

    return response


@router.post("/login/stop-impersonation")
async def stop_impersonation(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    # Must be impersonated
    if not current_user.get("impersonated"):
        raise HTTPException(status_code=400, detail="Not an impersonated session")

    original_user_id = current_user.get("impersonated_by")
    if not original_user_id:
        raise HTTPException(status_code=400, detail="Original user not found")

    # Load original user
    result = await db.execute(
        select(User).where(User.id == original_user_id)
    )
    original_user = result.scalar_one_or_none()

    if not original_user:
        raise HTTPException(status_code=404, detail="Original user no longer exists")

    # Create NEW token for original user
    token = create_access_token({
        "sub": original_user.email
    })

    fake_credentials = HTTPAuthorizationCredentials(
        scheme="bearer",
        credentials=token
    )

    permissions = await get_user_permissions_detailed(
        credentials=fake_credentials,
        db=db
    )

    # Reset cookies
    # response = RedirectResponse(
    #     url=f"{settings.root_path}/app/dashboard",
    #     status_code=302
    # )
    # Return JSON instead of RedirectResponse
    response = JSONResponse(content={
        "success": True,
        "message": "Impersonation stopped, returned to original user",
        "redirect_to": f"{settings.root_path}/app/dashboard",  # optional: tell frontend where to go
        "user_id": permissions["user_id"],
        "role": permissions["role"],
    })

    response.set_cookie("access_token", token, httponly=False, path=settings.root_path or "/")
    response.set_cookie("user_id", permissions["user_id"], httponly=False)
    response.set_cookie("role", permissions["role"], httponly=False)

    description = f"STOP IMPERSONATION: returned to user_id={original_user_id}"
    action = 'IMPERSONATION'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/impersonate/login/subscriber',
                        action= action, description= description, is_backend= True, input_params= original_user_id)
    

    logger.warning(
        f"STOP IMPERSONATION: returned to user_id={original_user_id}"
    )

    return response
