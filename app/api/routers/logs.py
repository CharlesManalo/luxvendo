"""Logs router - system log management."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Log
from api import schemas
from api.middleware import require_admin

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("", response_model=schemas.LogListResponse)
async def list_logs(
    level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get system logs with filtering."""
    query = select(Log)
    
    if level:
        query = query.where(Log.level == level)
    if category:
        query = query.where(Log.category == category)
    if search:
        query = query.where(Log.message.ilike(f"%{search}%"))
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.order_by(Log.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return schemas.LogListResponse(
        logs=[schemas.LogResponse.model_validate(l) for l in logs],
        total=total,
    )
