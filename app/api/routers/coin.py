"""Coin system router - coin payment integration (disabled by default)."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Setting, Voucher, Session as SessionModel, Log
from api import schemas
from api.middleware import require_api_key

router = APIRouter(prefix="/coin", tags=["Coin System"])


async def _is_enabled(db: AsyncSession) -> bool:
    """Check if coin system is enabled."""
    result = await db.execute(
        select(Setting).where(Setting.key == "coin_system_enabled")
    )
    setting = result.scalar_one_or_none()
    return setting is not None and setting.value.lower() == "true"


async def _get_price(db: AsyncSession) -> float:
    """Get coin price per minute."""
    result = await db.execute(
        select(Setting).where(Setting.key == "coin_price_per_minute")
    )
    setting = result.scalar_one_or_none()
    if setting:
        return float(setting.value)
    return 0.5


@router.get("/status", response_model=schemas.CoinStatusResponse)
async def coin_status(
    db: AsyncSession = Depends(get_db),
):
    """Get coin system status."""
    enabled = await _is_enabled(db)
    price = await _get_price(db)
    
    currency_result = await db.execute(
        select(Setting).where(Setting.key == "coin_currency")
    )
    currency_setting = currency_result.scalar_one_or_none()
    currency = currency_setting.value if currency_setting else "USD"
    
    return schemas.CoinStatusResponse(
        enabled=enabled,
        price_per_minute=price if enabled else None,
        currency=currency if enabled else None,
    )


@router.post("/payment")
async def record_coin_payment(
    data: schemas.CoinPaymentRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_api_key),
):
    """Record a coin payment and create voucher (for ESP32 integration)."""
    if not await _is_enabled(db):
        raise HTTPException(status_code=400, detail="Coin system is disabled")
    
    # Calculate minutes from amount
    price = await _get_price(db)
    expected_amount = data.minutes * price
    
    if abs(data.amount - expected_amount) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid amount. Expected {expected_amount} for {data.minutes} minutes",
        )
    
    # Create a voucher for this payment
    from api.routers.vouchers import get_unique_code
    code = await get_unique_code(db)
    
    voucher = Voucher(
        code=code,
        duration_minutes=data.minutes,
        status="active",
        created_by=None,  # System-generated
    )
    db.add(voucher)
    await db.flush()
    
    # Log the payment
    log = Log(
        level="info",
        category="coin",
        message=f"Coin payment: {data.amount} for {data.minutes}min, voucher {code}",
        details=json.dumps({
            "mac_address": data.mac_address,
            "amount": data.amount,
            "minutes": data.minutes,
            "voucher_code": code,
        }),
    )
    db.add(log)
    await db.commit()
    
    return {
        "success": True,
        "message": "Payment recorded",
        "voucher_code": code,
        "duration_minutes": data.minutes,
    }


@router.get("/price")
async def get_coin_price(
    db: AsyncSession = Depends(get_db),
):
    """Get current coin pricing."""
    enabled = await _is_enabled(db)
    price = await _get_price(db) if enabled else None
    
    currency_result = await db.execute(
        select(Setting).where(Setting.key == "coin_currency")
    )
    currency = currency_result.scalar_one_or_none()
    
    # Get voucher durations for pricing table
    durations_result = await db.execute(
        select(Setting).where(Setting.key == "voucher_durations")
    )
    durations_setting = durations_result.scalar_one_or_none()
    durations = json.loads(durations_setting.value) if durations_setting else [30, 60, 180, 1440]
    
    pricing_table = []
    for minutes in durations:
        if enabled:
            pricing_table.append({
                "minutes": minutes,
                "price": round(minutes * (price or 0.5), 2),
            })
        else:
            pricing_table.append({
                "minutes": minutes,
                "price": None,
            })
    
    return {
        "enabled": enabled,
        "price_per_minute": price,
        "currency": currency.value if currency else "USD",
        "pricing_table": pricing_table,
    }
