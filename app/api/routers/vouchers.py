"""Voucher router - CRUD, validate, activate, bulk generate."""
import random
import string
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Voucher, Session, User, Setting
from api import schemas
from api.middleware import require_admin, require_api_key, log_request

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])


def generate_voucher_code(length: int = 8) -> str:
    """Generate a random voucher code: XXXX-XXXX format."""
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=length))
    return f"{code[:4]}-{code[4:]}"


async def get_unique_code(db: AsyncSession, length: int = 8, max_attempts: int = 100) -> str:
    """Generate a unique voucher code that doesn't exist in DB."""
    for _ in range(max_attempts):
        code = generate_voucher_code(length)
        result = await db.execute(select(Voucher).where(Voucher.code == code))
        if result.scalar_one_or_none() is None:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate unique voucher code",
    )


@router.get("", response_model=schemas.VoucherListResponse)
async def list_vouchers(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List vouchers with optional filtering."""
    query = select(Voucher)
    
    if status_filter:
        query = query.where(Voucher.status == status_filter)
    
    if search:
        query = query.where(Voucher.code.ilike(f"%{search}%"))
    
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    # Get paginated results
    query = query.order_by(Voucher.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    vouchers = result.scalars().all()
    
    return schemas.VoucherListResponse(
        vouchers=[schemas.VoucherResponse.model_validate(v) for v in vouchers],
        total=total,
    )


@router.post("/generate", response_model=schemas.VoucherResponse)
async def generate_voucher(
    request: Request,
    data: schemas.VoucherCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Generate a new voucher."""
    if data.quantity == 1:
        code = await get_unique_code(db)
        voucher = Voucher(
            code=code,
            duration_minutes=data.duration_minutes,
            status="active",
            created_by=admin.id,
        )
        db.add(voucher)
        await db.commit()
        await db.refresh(voucher)
        
        await log_request(
            request, "voucher",
            f"Generated voucher {voucher.code} ({data.duration_minutes}min)"
        )
        
        return schemas.VoucherResponse.model_validate(voucher)
    else:
        # Bulk generate - return the first one
        return await bulk_generate_vouchers(request, data, db, admin)


@router.post("/bulk-generate", response_model=schemas.VoucherListResponse)
async def bulk_generate_vouchers(
    request: Request,
    data: schemas.VoucherCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Bulk generate vouchers."""
    vouchers = []
    for _ in range(data.quantity):
        code = await get_unique_code(db)
        voucher = Voucher(
            code=code,
            duration_minutes=data.duration_minutes,
            status="active",
            created_by=admin.id,
        )
        db.add(voucher)
        vouchers.append(voucher)
    
    await db.commit()
    
    for v in vouchers:
        await db.refresh(v)
    
    await log_request(
        request, "voucher",
        f"Bulk generated {data.quantity} vouchers ({data.duration_minutes}min each)"
    )
    
    return schemas.VoucherListResponse(
        vouchers=[schemas.VoucherResponse.model_validate(v) for v in vouchers],
        total=len(vouchers),
    )


@router.get("/{voucher_id}", response_model=schemas.VoucherResponse)
async def get_voucher(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get voucher details."""
    result = await db.execute(select(Voucher).where(Voucher.id == voucher_id))
    voucher = result.scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return schemas.VoucherResponse.model_validate(voucher)


@router.post("/{voucher_id}/disable")
async def disable_voucher(
    request: Request,
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Disable a voucher."""
    result = await db.execute(select(Voucher).where(Voucher.id == voucher_id))
    voucher = result.scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    voucher.status = "disabled"
    await db.commit()
    
    await log_request(request, "voucher", f"Disabled voucher {voucher.code}")
    
    return {"success": True, "message": f"Voucher {voucher.code} disabled"}


@router.delete("/{voucher_id}")
async def delete_voucher(
    request: Request,
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Delete a voucher."""
    result = await db.execute(select(Voucher).where(Voucher.id == voucher_id))
    voucher = result.scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    code = voucher.code
    await db.delete(voucher)
    await db.commit()
    
    await log_request(request, "voucher", f"Deleted voucher {code}")
    
    return {"success": True, "message": f"Voucher {code} deleted"}


# ─── Public endpoints (API key auth for captive portal) ───

@router.post("/validate", response_model=schemas.VoucherValidateResponse)
async def validate_voucher(
    request: Request,
    data: schemas.VoucherValidateRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_api_key),
):
    """Validate a voucher code (public endpoint for captive portal)."""
    result = await db.execute(
        select(Voucher).where(Voucher.code == data.code.upper().strip())
    )
    voucher = result.scalar_one_or_none()
    
    if not voucher:
        return schemas.VoucherValidateResponse(
            valid=False,
            message="Invalid voucher code",
        )
    
    if voucher.status == "used":
        return schemas.VoucherValidateResponse(
            valid=False,
            message="Voucher already used",
        )
    
    if voucher.status == "expired":
        return schemas.VoucherValidateResponse(
            valid=False,
            message="Voucher expired",
        )
    
    if voucher.status == "disabled":
        return schemas.VoucherValidateResponse(
            valid=False,
            message="Voucher disabled",
        )
    
    # Check if voucher has expired (has expires_at)
    if voucher.expires_at and voucher.expires_at < datetime.datetime.utcnow():
        voucher.status = "expired"
        await db.commit()
        return schemas.VoucherValidateResponse(
            valid=False,
            message="Voucher expired",
        )
    
    return schemas.VoucherValidateResponse(
        valid=True,
        message="Voucher valid",
        voucher=schemas.VoucherResponse.model_validate(voucher),
    )


@router.post("/activate")
async def activate_voucher(
    request: Request,
    data: schemas.VoucherActivateRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_api_key),
):
    """Activate voucher and create session (public endpoint for captive portal)."""
    # Find voucher
    result = await db.execute(
        select(Voucher).where(Voucher.code == data.code.upper().strip())
    )
    voucher = result.scalar_one_or_none()
    
    if not voucher or voucher.status != "active":
        raise HTTPException(status_code=400, detail="Invalid or used voucher")
    
    # Check coin system
    coin_result = await db.execute(
        select(Setting).where(Setting.key == "coin_system_enabled")
    )
    coin_setting = coin_result.scalar_one_or_none()
    if coin_setting and coin_setting.value.lower() == "true":
        # Coin system is enabled - payment should have been processed separately
        pass  # For now, allow activation (coin payment logic would be here)
    
    # Calculate expiry
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(minutes=voucher.duration_minutes)
    
    # Mark voucher as used
    voucher.status = "used"
    voucher.used_at = now
    voucher.expires_at = expiry
    voucher.used_by_mac = data.mac_address
    voucher.used_by_ip = data.ip_address
    
    # Create session
    session = Session(
        voucher_id=voucher.id,
        mac_address=data.mac_address,
        ip_address=data.ip_address,
        device_name=data.device_name,
        login_time=now,
        expiry_time=expiry,
        last_activity=now,
        status="active",
    )
    db.add(session)
    
    # Upsert user
    user_result = await db.execute(
        select(User).where(User.mac_address == data.mac_address)
    )
    user = user_result.scalar_one_or_none()
    if user:
        user.ip_address = data.ip_address
        user.device_name = data.device_name or user.device_name
        user.last_seen = now
        user.total_sessions += 1
    else:
        user = User(
            mac_address=data.mac_address,
            ip_address=data.ip_address,
            device_name=data.device_name,
            total_sessions=1,
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(session)
    
    await log_request(
        request, "session",
        f"Session created for MAC {data.mac_address} using voucher {voucher.code}"
    )
    
    return {
        "success": True,
        "message": "Voucher activated",
        "session_id": session.id,
        "expires_at": expiry.isoformat(),
        "duration_minutes": voucher.duration_minutes,
    }
