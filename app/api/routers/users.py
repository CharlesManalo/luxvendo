"""User router - manage WiFi users."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import User, Session as SessionModel
from api import schemas
from api.middleware import require_admin, log_request

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=schemas.UserListResponse)
async def list_users(
    request: Request,
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List all users with optional search."""
    query = select(User)
    
    if search:
        query = query.where(
            or_(
                User.mac_address.ilike(f"%{search}%"),
                User.ip_address.ilike(f"%{search}%"),
                User.device_name.ilike(f"%{search}%"),
            )
        )
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.order_by(User.last_seen.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return schemas.UserListResponse(
        users=[schemas.UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get user details with session history."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get session history
    sessions_result = await db.execute(
        select(SessionModel).where(SessionModel.mac_address == user.mac_address)
        .order_by(SessionModel.login_time.desc())
        .limit(20)
    )
    sessions = sessions_result.scalars().all()
    
    user_data = schemas.UserResponse.model_validate(user).model_dump()
    user_data["session_history"] = [
        {
            "id": s.id,
            "login_time": s.login_time.isoformat(),
            "expiry_time": s.expiry_time.isoformat() if s.expiry_time else None,
            "status": s.status,
            "data_usage_mb": s.data_usage_mb,
        }
        for s in sessions
    ]
    
    return user_data


@router.post("/{user_id}/blacklist")
async def blacklist_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Blacklist a user by MAC address."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_blacklisted = True
    await db.commit()
    
    # Also terminate any active sessions
    sessions_result = await db.execute(
        select(SessionModel).where(
            SessionModel.mac_address == user.mac_address,
            SessionModel.status == "active",
        )
    )
    for session in sessions_result.scalars().all():
        session.status = "terminated"
    
    await db.commit()
    
    await log_request(request, "user", f"Blacklisted user {user.mac_address}")
    
    return {"success": True, "message": f"User {user.mac_address} blacklisted"}


@router.post("/{user_id}/unblacklist")
async def unblacklist_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Remove user from blacklist."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_blacklisted = False
    await db.commit()
    
    await log_request(request, "user", f"Removed {user.mac_address} from blacklist")
    
    return {"success": True, "message": f"User {user.mac_address} removed from blacklist"}


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Delete a user record."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    mac = user.mac_address
    await db.delete(user)
    await db.commit()
    
    await log_request(request, "user", f"Deleted user {mac}")
    
    return {"success": True, "message": f"User {mac} deleted"}
