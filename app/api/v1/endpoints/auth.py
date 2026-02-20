from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import Token
from datetime import datetime, timedelta
import json
from app.crud.user import get_permissions_for_user, authenticate_user

router = APIRouter()

@router.post("/login")
async def login(
    response: Response,  # To set cookies properly
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    permissions = await get_permissions_for_user(db, user)
    print(permissions)

    # Set HTTP-only cookie for token (secure)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        expires=1800,
        secure=True,    # Set to False in dev if not using HTTPS
        samesite="lax"
    )

    # Set non-httponly cookies for frontend access
    response.set_cookie(
        key="user_role",
        value=permissions["role"] or "",
        max_age=1800,
        secure=True,
        samesite="lax"
    )
    response.set_cookie(
        key="user_menus",
        value=json.dumps(permissions["menus"]),
        max_age=1800,
        secure=True,
        samesite="lax"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": permissions["role"],
        "menus": permissions["menus"]
    }