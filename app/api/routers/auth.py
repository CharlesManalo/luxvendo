"""Authentication router - login, logout, me, setup."""
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Admin
from api import schemas
from api.auth import (
    hash_password,
    verify_password,
    create_session,
    get_session,
    delete_session,
)
from api.middleware import require_admin, optional_admin, log_request

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    request: Request,
    response: Response,
    data: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Admin login - returns session cookie."""
    result = await db.execute(
        select(Admin).where(
            Admin.username == data.username,
            Admin.is_active == True,
        )
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Create session
    token = create_session(admin.id)
    
    # Set cookie
    response.set_cookie(
        key="wifi_admin_session",
        value=token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=86400,
    )
    
    await log_request(request, "auth", f"Admin '{admin.username}' logged in")
    
    return schemas.LoginResponse(
        success=True,
        message="Login successful",
        admin=schemas.AdminResponse.model_validate(admin),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    """Clear session and logout."""
    token = request.cookies.get("wifi_admin_session")
    if token:
        delete_session(token)
    
    response.delete_cookie("wifi_admin_session")
    
    await log_request(request, "auth", "Admin logged out")
    
    return {"success": True, "message": "Logged out"}


@router.get("/me", response_model=schemas.AdminResponse)
async def get_me(admin: Admin = Depends(require_admin)):
    """Get current admin info."""
    return schemas.AdminResponse.model_validate(admin)


@router.post("/setup", response_model=schemas.LoginResponse)
async def setup(
    request: Request,
    response: Response,
    data: schemas.AdminCreate,
    db: AsyncSession = Depends(get_db),
):
    """First-run setup - create initial admin (only works if no admins exist)."""
    # Check if any admin exists
    result = await db.execute(select(Admin))
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup already completed. Use regular login.",
        )
    
    # Create admin
    admin = Admin(
        username=data.username,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    
    # Create session
    token = create_session(admin.id)
    response.set_cookie(
        key="wifi_admin_session",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )
    
    await log_request(request, "auth", f"Initial admin '{admin.username}' created")
    
    return schemas.LoginResponse(
        success=True,
        message="Setup complete",
        admin=schemas.AdminResponse.model_validate(admin),
    )


@router.get("/check-setup")
async def check_setup(db: AsyncSession = Depends(get_db)):
    """Check if initial setup is needed (no admins exist)."""
    result = await db.execute(select(Admin))
    admin = result.scalars().first()
    return {"needs_setup": admin is None}
