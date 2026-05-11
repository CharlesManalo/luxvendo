"""Settings router - manage system configuration."""
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Setting
from api import schemas
from api.middleware import require_admin, require_api_key

router = APIRouter(prefix="/settings", tags=["Settings"])


def _parse_setting_value(setting: Setting) -> Any:
    """Parse setting value based on its type."""
    if setting.type == "int":
        return int(setting.value)
    elif setting.type == "bool":
        return setting.value.lower() in ("true", "1", "yes")
    elif setting.type == "float":
        return float(setting.value)
    elif setting.type == "json":
        return json.loads(setting.value)
    return setting.value


@router.get("", response_model=list[schemas.SettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get all settings."""
    result = await db.execute(select(Setting).order_by(Setting.key))
    settings = result.scalars().all()
    return [schemas.SettingResponse.model_validate(s) for s in settings]


@router.get("/{key}", response_model=schemas.SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Get a specific setting."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return schemas.SettingResponse.model_validate(setting)


@router.post("")
async def update_settings(
    request: Request,
    data: schemas.SettingsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Update multiple settings at once."""
    updated = []
    
    for key, value in data.settings.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            setting.updated_by = admin.id
            updated.append(key)
        else:
            # Create new setting if it doesn't exist
            new_setting = Setting(
                key=key,
                value=value,
                type="string",
            )
            db.add(new_setting)
            updated.append(key)
    
    await db.commit()
    
    from api.middleware import log_request
    await log_request(request, "settings", f"Updated settings: {', '.join(updated)}")
    
    return {"success": True, "message": f"Updated {len(updated)} settings", "updated": updated}


@router.get("/public/config")
async def get_public_settings(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_api_key),
):
    """Get public settings for captive portal (no auth required, uses API key)."""
    keys = ["portal_name", "coin_system_enabled", "maintenance_mode", "voucher_durations"]
    settings = {}
    
    for key in keys:
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            settings[key] = _parse_setting_value(setting)
        else:
            settings[key] = None
    
    return schemas.PublicSettingsResponse(
        portal_name=settings.get("portal_name", "Free WiFi"),
        coin_system_enabled=settings.get("coin_system_enabled", False),
        maintenance_mode=settings.get("maintenance_mode", False),
        voucher_durations=settings.get("voucher_durations", [30, 60, 180, 1440]),
    )
