"""Seed initial data into the database."""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Admin, Setting
from api.auth import hash_password


async def seed_database(db: AsyncSession):
    """Seed default data if tables are empty."""
    
    # Check if admin exists
    result = await db.execute(select(Admin))
    if result.scalars().first() is None:
        # Create default admin
        default_admin = Admin(
            username="admin",
            password_hash=hash_password("admin123"),
            is_active=True,
        )
        db.add(default_admin)
    
    # Seed default settings
    default_settings = [
        {
            "key": "portal_name",
            "value": "Free WiFi",
            "type": "string",
            "description": "WiFi portal display name",
        },
        {
            "key": "session_timeout",
            "value": "1440",
            "type": "int",
            "description": "Default session timeout in minutes",
        },
        {
            "key": "max_devices",
            "value": "50",
            "type": "int",
            "description": "Maximum concurrent devices",
        },
        {
            "key": "coin_system_enabled",
            "value": "false",
            "type": "bool",
            "description": "Enable coin payment system",
        },
        {
            "key": "maintenance_mode",
            "value": "false",
            "type": "bool",
            "description": "Enable maintenance mode",
        },
        {
            "key": "voucher_durations",
            "value": json.dumps([30, 60, 180, 1440]),
            "type": "json",
            "description": "Available voucher durations in minutes",
        },
        {
            "key": "coin_price_per_minute",
            "value": "0.5",
            "type": "float",
            "description": "Coin price per minute of WiFi access",
        },
        {
            "key": "coin_currency",
            "value": "USD",
            "type": "string",
            "description": "Currency for coin payments",
        },
    ]
    
    for setting_data in default_settings:
        result = await db.execute(select(Setting).where(Setting.key == setting_data["key"]))
        if result.scalar_one_or_none() is None:
            setting = Setting(**setting_data)
            db.add(setting)
    
    await db.commit()
