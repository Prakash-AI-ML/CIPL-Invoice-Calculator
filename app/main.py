import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, status, HTTPException, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

from app.core.config import settings, engine, AsyncSessionLocal
from app.db.base_class import Base
from app.db.session import get_db
from app.api import router as api_router
from app.api.dependencies import get_user_permissions_detailed
from app.api.deps import get_current_user_from_request
from app.crud.user import authenticate_user, get_user_by_email, get_user_by_username
from app.core.security import create_access_token, create_password_reset_token, verify_password_reset_token, get_password_hash
from app.core.email import send_reset_email
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json
import logging
from pathlib import Path

from app.crud.log_manage import logs, frontend_logs

# Async DB init function
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Global scheduler
scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)  # Change timezone if needed


async def trigger_daily_reminder():
    """Internally call the /reminder-email endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.scheduler_reminder_url)
            logger.info(f"Daily reminder job executed: {response.status_code} - {response.json()}")
        except Exception as e:
            logger.error(f"Failed to trigger daily reminder: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database initialization
    await init_db()

    worker_index = int(os.getenv("PYTHON_WORKER_INDEX", "1"))
    is_scheduler_worker = worker_index == 1
    if is_scheduler_worker:
        # Start scheduler and add daily job
        scheduler.add_job(
            trigger_daily_reminder,
            trigger="cron",
            hour=settings.scheduler_hour,
            minute=settings.scheduler_minute,
            second=0,
            day_of_week='mon-sat',
            id="daily_due_today_reminder",
            replace_existing=True,
            coalesce=True,
            timezone=settings.scheduler_timezone
        )
    
        scheduler.start()
        logger.info(
            f"APScheduler STARTED on worker {worker_index} - "
            f"Reminder scheduled Mon–Sat at {settings.scheduler_hour:02d}:{settings.scheduler_minute:02d} "
            f"({settings.scheduler_timezone})"
        )
    else:
        logger.info(f"APScheduler SKIPPED on worker {worker_index} - only worker 1 runs it")
    yield

    # Shutdown: stop scheduler and dispose engine
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shut down")
    await engine.dispose()

# Logging setup
log_dir = Path("app/logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# App with root_path (auto-prefixes URLs for /soa proxy)
app = FastAPI(
    title="Async FastAPI Auth App",
    lifespan=lifespan,
    root_path=settings.root_path  # NEW: /soa (from .env); empty for local
)

# Mount static files (/soa/static/ with root_path)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include API router (/soa/api/v1/... with root_path)
app.include_router(api_router)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only protect routes under /app/
        if request.url.path.startswith("/app/"):
            # Get token from cookie (your login sets it in cookie)
            token = request.cookies.get("access_token")
            if not token:
                return RedirectResponse(url=f"{settings.root_path}/", status_code=302)

            # Create fake credentials object expected by the dependency
            fake_credentials = HTTPAuthorizationCredentials(
                scheme="bearer",
                credentials=token
            )

            # Use your existing dependency to get full permissions
            try:
                async with AsyncSessionLocal() as db:
                    permissions = await get_user_permissions_detailed(
                        credentials=fake_credentials,
                        db=db  # Will be injected by Depends inside the dependency
                    )
            except HTTPException:
                # Invalid token or user not found → redirect to login
                return RedirectResponse(url=f"{settings.root_path}/", status_code=302)

            # Attach full permissions to request.state.user for templates/middleware
            request.state.user = permissions

        # Continue to next middleware/endpoint
        response: Response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

@app.middleware("http")
async def allow_iframe(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "frame-ancestors https://payable.pixxa.tech:8080/ http://localhost:8000" 
    )
    return response

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):

    await frontend_logs(request= request, endpoint='/', description=f'Login page accessed via: {request.url}', action='Login page')
    logger.info(f"Login page accessed via: {request.url}")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_template(
    request: Request,
    email: str = Form(...),  # FIXED: Direct email (update template name="email")
    password: str = Form(...)
):
    logger.info(f"Login attempt for email: {email}")
    async for db in get_db():
        user = await authenticate_user(db, email, password)
        if not user:
            logger.warning(f"Failed login for email: {email}")
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})
        
        token = create_access_token({"sub": user.email})

        fake_credentials = HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials=token
        )

        # Call the dependency to get full permissions
        try:
            permissions = await get_user_permissions_detailed(
                credentials=fake_credentials,
                db=db
            )
        except HTTPException as exc:
            # If something goes wrong with permissions, still log in but without detailed perms
            logger.error(f"Failed to load permissions for {email}: {exc.detail}")
            permissions = {
                "user_id": user.id,
                "role": user.role.role_name if user.role else "Unknown",
                "menus": {}
            }
        
        response = RedirectResponse(url=f"{settings.root_path}/app/dashboard", status_code=302)  # Becomes /soa/app/aging
        response.set_cookie(key="access_token", value=token, httponly=False, path=settings.root_path or "/")
        response.set_cookie(key="root_path", value=settings.root_path, httponly=False )
        response.set_cookie(
            key="user_id",
            value=permissions.get("user_id", 1),
            httponly=False,          # JS needs to read for UI
            secure=True,
            samesite="lax",
            path=settings.root_path or "/",
            # max_age=settings.access_token_expire_minutes
        )
        response.set_cookie(
            key="role",
            value=permissions.get("role", "Unknown"),
            httponly=False,          # JS needs to read for UI
            secure=True,
            samesite="lax",
            path=settings.root_path or "/",
            # max_age=settings.access_token_expire_minutes
        )

      
        logger.info(f"Successful login for {email}, redirecting to /app/dashboard")
        return response

@app.get("/logout")
async def logout(request: Request):
    description = f"Logout for user from: {request.url}"
    # await logs(request = request, endpoint='/app/logout', action= 'logout', description= description, is_backend= False)
    logger.info(f"Logout for user from: {request.url}")
    response = RedirectResponse(url=f"{settings.root_path}/", status_code=302)  # Becomes /soa/login
    # response.delete_cookie("access_token")
    for key_ in ['access_token', 'user_id', 'role', 'root_path']:
        response.delete_cookie(key = key_, path = settings.root_path or "/")
    return response

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    await frontend_logs(request= request, endpoint='/forgot-password', description=f'Forgot Password page accessed via: {request.url}', action='Forgot Password page')
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    identity: str = Form(...)
):
    await frontend_logs(request= request,endpoint='/forgot-password', description=f'Forgot Password page accessed via: {request.url}', action='Forgot Password Submit', input_params= identity)

    async for db in get_db():
        user = await get_user_by_username(db, identity) or await get_user_by_email(db, identity)
        
        if not user:
            # Security: don't reveal existence
            return templates.TemplateResponse("forgot_password.html", {
                "request": request,
                "message": "If an account exists, a reset link has been sent."
            })

        token = create_password_reset_token(user.username, timedelta(minutes=15))
        reset_url = f"{request.base_url}reset-password?token={token}"

        # Send email (dev logs to console, prod sends real email)
        await send_reset_email(user.email, user.username, reset_url)

        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "message": "If an account exists, a reset link has been sent."
        })

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None):
    await frontend_logs(request= request, endpoint='/reset-password', description=f'Reset Password page accessed via: {request.url}', action='Reset Password page', input_params= token)
    if not token:
        return RedirectResponse(f"{settings.root_path}/forgot-password")

    username = verify_password_reset_token(token)
    if not username:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Invalid or expired reset link."
        })

    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "token": token
    })

@app.post("/reset-password")
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    data = {'token':token, 'password': password + password_confirm}
    await frontend_logs(request= request, endpoint='/reset-password', description=f'Reset Password submit accessed via: {request.url}', action='Reset Password submit', input_params= data)

    if password != password_confirm:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "token": token,
            "error": "Passwords do not match."
        })

    if len(password) < 1:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "token": token,
            "error": "Password must be at least 6 characters."
        })

    username = verify_password_reset_token(token)
    if not username:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Invalid or expired token."
        })

    async for db in get_db():
        user = await get_user_by_username(db, username)
        if not user:
            return RedirectResponse(f"{settings.root_path}/")

        # Update password
        hashed = get_password_hash(password)
        user.hashed_password = hashed
        await db.commit()

    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "Password reset successfully! Please log in."
    })

@app.get("/app/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    description = "Profile page accessed"
    await logs(request = request, endpoint='/app/profile', action= 'profile', description= description, is_backend= False)
    logger.info(f"Profile accessed by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

# Protected routes (auto-prefixed)
@app.get("/app/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    description = "Dashboard page accessed"
    await logs(request = request, endpoint='/app/dashboard', action= 'dashboard', description= description, is_backend= False)
    return templates.TemplateResponse("index.html", {"request": request})

# Protected routes (auto-prefixed)
@app.get("/app/v1/dash", response_class=HTMLResponse)
async def dashboard(request: Request):
    description = "Dashboard page accessed"
    await logs(request = request, endpoint='/app/v1/dash', action= 'dashboard', description= description, is_backend= False)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/users", response_class=HTMLResponse)
async def users_page(request: Request, current_user=Depends(get_current_user_from_request)):
    if current_user and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/app/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    description = "Settings page accessed"
    await logs(request = request, endpoint='/app/settings', action= 'settings', description= description, is_backend= False)
    logger.info(f"Settings accessed by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/cipl", response_class=HTMLResponse)
async def user_list(request: Request):
    description = "Navigated to Users page from CIPL"
    await logs(request = request, endpoint='/app/cipl', action= 'cipl', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from CIPL by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/invoices", response_class=HTMLResponse)
async def user_list(request: Request):
    description = "Navigated to Users page from CIPL"
    await logs(request = request, endpoint='/app/cipl', action= 'cipl', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from CIPL by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/delivery-order", response_class=HTMLResponse)
async def user_list(request: Request):
    description = "Navigated to Users page from delivery-order"
    await logs(request = request, endpoint='/app/delivery-order', action= 'delivery-order', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from delivery-order by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/tally", response_class=HTMLResponse)
async def tally_page(request: Request):
    description = "Navigated to Users page from tally"
    await logs(request = request, endpoint='/app/tally', action= 'tally', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from tally by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/settings/users_list", response_class=HTMLResponse)
async def user_list(request: Request):
    description = "Navigated to Users page from Settings"
    await logs(request = request, endpoint='/app/settings/users_list', action= 'users_list', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from Settings by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/settings/descriptions", response_class=HTMLResponse)
async def user_list(request: Request):
    description = "Navigated to Users page from Settings"
    await logs(request = request, endpoint='/app/settings/cipl-descriptions', action= 'cipl-descriptions', description= description, is_backend= False)
    logger.info(f"Navigated to Users page from Settings by user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/app/settings/role", response_class=HTMLResponse)
async def role_list(request: Request):
    description = "Navigated to Role page from Settings"
    await logs(request = request, endpoint='/app/settings/role', action= 'role', description= description, is_backend= False)
    logger.info(f"Navigated to Role page from Settings user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/settings/category", response_class=HTMLResponse)
async def category_list(request: Request):
    description = "Navigated to Category page from Settings"
    await logs(request = request, endpoint='/app/settings/category', action= 'category', description= description, is_backend= False)
    logger.info(f"Navigated to Category page from Settings user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/settings/clients", response_class=HTMLResponse)
async def clients_list(request: Request):
    description = "Navigated to Clients page from Settings"
    await logs(request = request, endpoint='/app/settings/clients', action= 'clients', description= description, is_backend= False)
    logger.info(f"Navigated to Clients page from Settings user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/menu", response_class=HTMLResponse)
async def menu_list(request: Request):
    description = "Navigated to Menu page from Settings"
    await logs(request = request, endpoint='/app/settings/menu', action= 'menu', description= description, is_backend= False)
    logger.info(f"Navigated to Menu page from Settings user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/button", response_class=HTMLResponse)
async def button_list(request: Request):
    description = "Navigated to Button page from Settings"
    await logs(request = request, endpoint='/app/settings/button', action= 'button', description= description, is_backend= False)
    logger.info(f"Navigated to Button page from Settings user: {request.state.user.get('username', 'unknown')}")
    return templates.TemplateResponse("index.html", {"request": request})

# Startup log
@app.on_event("startup")
async def startup_event():
    logger.info("SOA app started with root_path: %s", settings.root_path)