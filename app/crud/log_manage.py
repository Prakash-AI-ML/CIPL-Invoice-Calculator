from user_agents import parse
from app.models.logs import ActivityLog
from app.core.config import AsyncSessionLocal  # Your async session factory

async def logs(request, endpoint: str, action: str, description: str, is_backend: bool = True, input_params=None):
    # ─── Get client IP ─────────────────────────────
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    # ─── Parse user agent ──────────────────────────
    user_agent_str = request.headers.get("user-agent", "")
    ua = parse(user_agent_str)

    # ─── Build log info ───────────────────────────
    client_info = {
        "subscriber_id": request.state.user.get('user_id', None),
        "subscriber_name": request.state.user.get('username', None),
        "subscriber_email": request.state.user.get('email', None),
        "subscriber_role": request.state.user.get('role', None),
        "endpoint": endpoint,
        "action": action,
        "description": description,
        "ip": client_ip,
        "port": request.client.port if request.client else None,
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
        "os": ua.os.family,
        "os_version": ua.os.version_string,
        "device": ua.device.family,
        "is_mobile": ua.is_mobile,
        "is_tablet": ua.is_tablet,
        "is_pc": ua.is_pc,
        "is_bot": ua.is_bot,
        "method": request.method,
        "path": request.url.path,
        "referer": request.headers.get("referer"),
        "origin": request.headers.get("origin"),
        "is_backend": 1 if is_backend else 0,
        "params": input_params
    }

    # ─── Insert into database ─────────────────────
    async with AsyncSessionLocal() as session:
        activity = ActivityLog(**client_info)
        session.add(activity)
        await session.commit()  # Commit immediately






async def backend_logs(request, current_user, endpoint: str, action: str, description: str, is_backend: bool = True, input_params=None):
    # ─── Get client IP ─────────────────────────────
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    # ─── Parse user agent ──────────────────────────
    user_agent_str = request.headers.get("user-agent", "")
    ua = parse(user_agent_str)

    # ─── Build log info ───────────────────────────
    client_info = {
        "subscriber_id": current_user.get('user_id', None),
        "subscriber_name": current_user.get('username', None),
        "subscriber_email": current_user.get('email', None),
        "subscriber_role": current_user.get('role', None),
        "impersonated_by": current_user.get('impersonated_by', None),
        "endpoint": endpoint,
        "action": action,
        "description": description,
        "ip": client_ip,
        "port": request.client.port if request.client else None,
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
        "os": ua.os.family,
        "os_version": ua.os.version_string,
        "device": ua.device.family,
        "is_mobile": ua.is_mobile,
        "is_tablet": ua.is_tablet,
        "is_pc": ua.is_pc,
        "is_bot": ua.is_bot,
        "method": request.method,
        "path": request.url.path,
        "referer": request.headers.get("referer"),
        "origin": request.headers.get("origin"),
        "is_backend": 1 if is_backend else 0,
        "params": input_params
    }

    # ─── Insert into database ─────────────────────
    async with AsyncSessionLocal() as session:
        activity = ActivityLog(**client_info)
        session.add(activity)
        await session.commit()  # Commit immediately




async def frontend_logs(request, endpoint: str, action: str, description: str, is_backend: bool = False, input_params=None):
    # print(request.__dict__)

    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else None

    # ─── Parse user agent ──────────────────────────
    user_agent_str = request.headers.get("user-agent", "")
    ua = parse(user_agent_str)

    # ─── Build log info ───────────────────────────
    client_info = {
        
        "endpoint": endpoint,
        "action": action,
        "description": description,
        "ip": client_ip,
        "port": request.client.port if request.client else None,
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
        "os": ua.os.family,
        "os_version": ua.os.version_string,
        "device": ua.device.family,
        "is_mobile": ua.is_mobile,
        "is_tablet": ua.is_tablet,
        "is_pc": ua.is_pc,
        "is_bot": ua.is_bot,
        "method": request.method,
        "path": request.url.path,
        "referer": request.headers.get("referer"),
        "origin": request.headers.get("origin"),
        "is_backend": 1 if is_backend else 0,
        "params": input_params
    }

    # ─── Insert into database ─────────────────────
    async with AsyncSessionLocal() as session:
        activity = ActivityLog(**client_info)
        session.add(activity)
        await session.commit()  # Commit immediately



