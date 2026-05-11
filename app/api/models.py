"""SQLAlchemy models for the WiFi Voucher System."""
import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey,
    create_engine
)
from api.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="active")  # active, used, expired, disabled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
    used_by_mac = Column(String(17), nullable=True)
    used_by_ip = Column(String(45), nullable=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    mac_address = Column(String(17), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    device_name = Column(String(100), nullable=True)
    login_time = Column(DateTime, default=datetime.datetime.utcnow)
    expiry_time = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="active")  # active, expired, terminated, paused
    data_usage_mb = Column(Float, default=0.0)
    is_paused = Column(Boolean, default=False)
    paused_at = Column(DateTime, nullable=True)
    paused_duration = Column(Integer, default=0)  # seconds


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    device_name = Column(String(100), nullable=True)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    total_sessions = Column(Integer, default=0)
    total_time_used = Column(Integer, default=0)  # minutes
    is_blacklisted = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    type = Column(String(20), default="string")  # string, int, bool, float, json
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("admins.id"), nullable=True)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), default="info")  # debug, info, warning, error
    category = Column(String(50), nullable=False)  # voucher, session, auth, system, settings
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
