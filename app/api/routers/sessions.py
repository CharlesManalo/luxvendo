"""Session router - manage active WiFi sessions."""
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Session as SessionModel, Voucher, User, Log
from api import schemas
from api.middleware import require_admin, log_request

router = APIRouter(prefix="/sessions", tags=["Sessions"])


async def _enrich_session(session, db):
    """Add computed fields to a session."""
    now = datetime.datetime.utcnow()
    remaining = (session.expiry_time - now).total_seconds() / 60 if session.expiry_time else 0
    if remaining < 0:
        remaining = 0
    
    voucher_code = None
    if session.voucher_id:
        result = await db.execute(
            select(Voucher.code).where(Voucher.id == session.voucher_id)
        )
        voucher_code = result.scalar()
    
    data = schemas.SessionResponse.model_validate(session)
    data.remaining_minutes = round(remaining, 1)
    data.voucher_code = voucher_code
    return data


@router.get("", response_model=schemas.SessionListResponse)
async def list_sessions(
    request: Request,
    status_filter: Optional[str] = Query("active", alias="status"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List sessions with filtering."""
    query = select(SessionModel)
    
    if status_filter:
        query = query.where(SessionModel.status == status_filter)
    
    if search:
        query = query.where(
            or_(
                SessionModel.mac_address.ilike(f"%{search}%"),
                SessionModel.ip_address.ilike(f"%{search}%"),
                SessionModel.device_name.ilike(f"%{search}%"),
            )
        )
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.order_by(SessionModel.login_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    enriched = []
    for s in sessions:
        enriched.append(await _enrich_session(s, db))
    
    return schemas.SessionListResponse(sessions=enriched, total=total)


@router.get("/history", response_model=schemas.SessionListResponse)
async def list_session_history(
    request: Request,
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List expired/terminated session history."""
    query = select(SessionModel).where(
        or_(SessionModel.status == "expired", SessionModel.status == "terminated")
    )
    
    if search:
        query = query.where(
            or_(
                SessionModel.mac_address.ilike(f"%{search}%"),
                SessionModel.ip_address.ilike(f"%{search}%"),
            )
        )
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.order_by(SessionModel.login_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    enriched = []
    for s in sessions:
        enriched.append(await _enrich_session(s, db))
    
    return schemas.SessionListResponse(sessions=enriched, total=total)


@router.get("/{session_id}", response_model=schemas.SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get session details."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return await _enrich_session(session, db)


@router.post("/{session_id}/terminate")
async def terminate_session(
    request: Request,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Terminate a session (kick user)."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status in ("expired", "terminated"):
        raise HTTPException(status_code=400, detail="Session already ended")
    
    session.status = "terminated"
    session.is_paused = False
    
    # Update voucher if exists
    if session.voucher_id:
        voucher_result = await db.execute(
            select(Voucher).where(Voucher.id == session.voucher_id)
        )
        voucher = voucher_result.scalar_one_or_none()
        if voucher:
            voucher.status = "expired"
    
    await db.commit()
    
    await log_request(
        request, "session",
        f"Session {session_id} for MAC {session.mac_address} terminated by admin"
    )
    
    return {"success": True, "message": f"Session {session_id} terminated"}


@router.post("/{session_id}/pause")
async def pause_session(
    request: Request,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Pause a session."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Can only pause active sessions")
    
    session.is_paused = True
    session.paused_at = datetime.datetime.utcnow()
    session.status = "paused"
    
    await db.commit()
    
    await log_request(request, "session", f"Session {session_id} paused")
    
    return {"success": True, "message": f"Session {session_id} paused"}


@router.post("/{session_id}/resume")
async def resume_session(
    request: Request,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Resume a paused session."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.is_paused:
        raise HTTPException(status_code=400, detail="Session is not paused")
    
    # Extend expiry time by the duration the session was paused
    if session.paused_at:
        paused_duration = (datetime.datetime.utcnow() - session.paused_at).total_seconds()
        session.paused_duration += int(paused_duration)
        session.expiry_time += datetime.timedelta(seconds=int(paused_duration))
    
    session.is_paused = False
    session.paused_at = None
    session.status = "active"
    session.last_activity = datetime.datetime.utcnow()
    
    await db.commit()
    
    await log_request(request, "session", f"Session {session_id} resumed")
    
    return {"success": True, "message": f"Session {session_id} resumed"}


@router.post("/{session_id}/extend")
async def extend_session(
    request: Request,
    session_id: int,
    data: schemas.SessionExtendRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Extend session time."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status in ("expired", "terminated"):
        raise HTTPException(status_code=400, detail="Cannot extend ended sessions")
    
    session.expiry_time += datetime.timedelta(minutes=data.additional_minutes)
    
    await db.commit()
    
    await log_request(
        request, "session",
        f"Session {session_id} extended by {data.additional_minutes} minutes"
    )
    
    return {
        "success": True,
        "message": f"Session extended by {data.additional_minutes} minutes",
        "new_expiry": session.expiry_time.isoformat(),
    }


@router.get("/stats/overview")
async def session_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get session statistics."""
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Active sessions count
    active_result = await db.execute(
        select(func.count()).where(SessionModel.status == "active")
    )
    active_count = active_result.scalar()
    
    # Paused sessions count
    paused_result = await db.execute(
        select(func.count()).where(SessionModel.status == "paused")
    )
    paused_count = paused_result.scalar()
    
    # Today's new sessions
    today_result = await db.execute(
        select(func.count()).where(SessionModel.login_time >= today_start)
    )
    today_count = today_result.scalar()
    
    # Expired today
    expired_result = await db.execute(
        select(func.count()).where(
            and_(
                SessionModel.status == "expired",
                SessionModel.expiry_time >= today_start,
            )
        )
    )
    expired_count = expired_result.scalar()
    
    return {
        "active": active_count,
        "paused": paused_count,
        "today": today_count,
        "expired_today": expired_count,
    }
