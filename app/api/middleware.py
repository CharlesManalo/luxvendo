"""FastAPI middleware - auth and API key validation."""
import datetime
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database import AsyncSessionLocal
from api.auth import get_session
from api.config import API_KEY
from api.models import Admin, Log

security = HTTPBearer(auto_error=False)


async def get_db_session():
    """Get DB session for middleware (manual commit)."""
    async with AsyncSessionLocal() as session:
        yield session


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Admin:
    """Dependency to require admin authentication via session cookie."""
    token = request.cookies.get("wifi_admin_session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    session_data = get_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    
    result = await db.execute(
        select(Admin).where(Admin.id == session_data["admin_id"], Admin.is_active == True)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive",
        )
    
    # Attach admin to request state
    request.state.admin = admin
    return admin


async def optional_admin(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Admin | None:
    """Optional admin auth - returns admin if logged in, None otherwise."""
    token = request.cookies.get("wifi_admin_session")
    if not token:
        return None
    
    session_data = get_session(token)
    if not session_data:
        return None
    
    result = await db.execute(
        select(Admin).where(Admin.id == session_data["admin_id"], Admin.is_active == True)
    )
    return result.scalar_one_or_none()


async def require_api_key(request: Request) -> bool:
    """Dependency to require API key for router endpoints."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # Also check query param
        api_key = request.query_params.get("api_key")
    
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True


async def log_request(
    request: Request,
    category: str,
    message: str,
    level: str = "info",
    details: str | None = None,
):
    """Log an action to the database."""
    try:
        async with AsyncSessionLocal() as db:
            log = Log(
                level=level,
                category=category,
                message=message,
                details=details,
                ip_address=request.client.host if request.client else None,
            )
            db.add(log)
            await db.commit()
    except Exception:
        pass  # Don't fail if logging fails
