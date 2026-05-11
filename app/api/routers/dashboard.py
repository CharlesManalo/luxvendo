"""Dashboard router - statistics and analytics."""
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import (
    Session as SessionModel,
    Voucher,
    User,
    Setting,
    Log,
)
from api.middleware import require_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get dashboard overview statistics."""
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Active sessions
    active_result = await db.execute(
        select(func.count()).where(
            or_(SessionModel.status == "active", SessionModel.status == "paused")
        )
    )
    active_sessions = active_result.scalar()
    
    # Total vouchers
    total_vouchers_result = await db.execute(select(func.count()).select_from(Voucher))
    total_vouchers = total_vouchers_result.scalar()
    
    # Used vouchers today
    used_today_result = await db.execute(
        select(func.count()).where(
            and_(Voucher.status == "used", Voucher.used_at >= today_start)
        )
    )
    used_today = used_today_result.scalar()
    
    # Expired sessions today
    expired_today_result = await db.execute(
        select(func.count()).where(
            and_(
                SessionModel.status == "expired",
                SessionModel.expiry_time >= today_start,
            )
        )
    )
    expired_today = expired_today_result.scalar()
    
    # Total users
    total_users_result = await db.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()
    
    # System status
    maintenance_result = await db.execute(
        select(Setting).where(Setting.key == "maintenance_mode")
    )
    maint_setting = maintenance_result.scalar_one_or_none()
    system_status = "maintenance" if (maint_setting and maint_setting.value.lower() == "true") else "online"
    
    # Available (unused active) vouchers
    available_result = await db.execute(
        select(func.count()).where(Voucher.status == "active")
    )
    available_vouchers = available_result.scalar()
    
    return {
        "active_sessions": active_sessions,
        "total_vouchers": total_vouchers,
        "available_vouchers": available_vouchers,
        "used_today": used_today,
        "expired_sessions_today": expired_today,
        "total_users": total_users,
        "system_status": system_status,
        "timestamp": now.isoformat(),
    }


@router.get("/activity")
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get recent activity feed (logs)."""
    result = await db.execute(
        select(Log).order_by(Log.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/usage")
async def get_usage_data(
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get usage data for chart (sessions per hour)."""
    now = datetime.datetime.utcnow()
    start_time = now - datetime.timedelta(hours=hours)
    
    # Get sessions in time range grouped by hour
    result = await db.execute(
        select(
            func.strftime("%Y-%m-%d %H:00", SessionModel.login_time).label("hour"),
            func.count().label("count"),
        )
        .where(SessionModel.login_time >= start_time)
        .group_by("hour")
        .order_by("hour")
    )
    
    data_points = []
    for row in result.all():
        data_points.append({
            "hour": row.hour,
            "sessions": row.count,
            "data_usage_mb": 0,  # Placeholder - would need actual traffic data
        })
    
    return {
        "period_hours": hours,
        "data": data_points,
    }


@router.get("/voucher-stats")
async def get_voucher_statistics(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get voucher distribution statistics."""
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - datetime.timedelta(days=7)
    
    # By status
    status_result = await db.execute(
        select(Voucher.status, func.count())
        .group_by(Voucher.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}
    
    # By duration
    duration_result = await db.execute(
        select(Voucher.duration_minutes, func.count())
        .group_by(Voucher.duration_minutes)
    )
    by_duration = {str(row[0]): row[1] for row in duration_result.all()}
    
    # Created today
    created_today_result = await db.execute(
        select(func.count()).where(Voucher.created_at >= today_start)
    )
    created_today = created_today_result.scalar()
    
    # Created this week
    created_week_result = await db.execute(
        select(func.count()).where(Voucher.created_at >= week_start)
    )
    created_week = created_week_result.scalar()
    
    return {
        "by_status": by_status,
        "by_duration": by_duration,
        "created_today": created_today,
        "created_this_week": created_week,
    }
