from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import verify_token, TokenData
from ..crud.user import get_user_by_email  # Changed from get_user_by_username
from ..db.session import get_db
from ..models.user import UserRole

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    token = credentials.credentials
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_email(db, email=token_data.email)  # Changed to email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user.id, "username": user.username, "role": "super_admin"}  # Keep username for display

def require_role(required_role: UserRole):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_any_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# For template routes
async def get_current_user_from_request(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token") or (request.headers.get("Authorization", "") or "").replace("Bearer ", "")
    if not token:
        return None
    token_data = verify_token(token)
    if not token_data:
        return None
    user = await get_user_by_email(db, email=token_data.email)  # Changed to email
    if user:
        return {"id": user.id, "username": user.username, 'role': 'super_admin'}
    return None