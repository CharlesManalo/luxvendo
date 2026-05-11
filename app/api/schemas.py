"""Pydantic v2 schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────
# Admin Schemas
# ──────────────────────────────
class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class AdminCreate(AdminBase):
    password: str = Field(..., min_length=6, max_length=100)


class AdminResponse(AdminBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────
# Auth Schemas
# ──────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    admin: Optional[AdminResponse] = None


# ──────────────────────────────
# Voucher Schemas
# ──────────────────────────────
class VoucherBase(BaseModel):
    code: str = Field(..., max_length=20)
    duration_minutes: int = Field(..., gt=0)


class VoucherCreate(BaseModel):
    duration_minutes: int = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1, le=100)


class VoucherResponse(BaseModel):
    id: int
    code: str
    duration_minutes: int
    status: str
    created_at: datetime
    used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_by: Optional[int]
    used_by_mac: Optional[str]
    used_by_ip: Optional[str]

    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    vouchers: List[VoucherResponse]
    total: int


class VoucherValidateRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=20)


class VoucherActivateRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=20)
    mac_address: str = Field(..., max_length=17)
    ip_address: str = Field(..., max_length=45)
    device_name: Optional[str] = Field(default=None, max_length=100)


class VoucherValidateResponse(BaseModel):
    valid: bool
    message: str
    voucher: Optional[VoucherResponse] = None


# ──────────────────────────────
# Session Schemas
# ──────────────────────────────
class SessionResponse(BaseModel):
    id: int
    voucher_id: int
    mac_address: str
    ip_address: str
    device_name: Optional[str]
    login_time: datetime
    expiry_time: datetime
    last_activity: datetime
    status: str
    data_usage_mb: float
    is_paused: bool
    paused_at: Optional[datetime]
    paused_duration: int
    # Computed fields
    remaining_minutes: Optional[float] = None
    voucher_code: Optional[str] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class SessionExtendRequest(BaseModel):
    additional_minutes: int = Field(..., gt=0, le=1440)


# ──────────────────────────────
# User Schemas
# ──────────────────────────────
class UserBase(BaseModel):
    mac_address: str = Field(..., max_length=17)
    ip_address: str = Field(..., max_length=45)
    device_name: Optional[str] = Field(default=None, max_length=100)


class UserResponse(UserBase):
    id: int
    first_seen: datetime
    last_seen: datetime
    total_sessions: int
    total_time_used: int
    is_blacklisted: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class UserUpdateRequest(BaseModel):
    notes: Optional[str] = None
    is_blacklisted: Optional[bool] = None


# ──────────────────────────────
# Setting Schemas
# ──────────────────────────────
class SettingBase(BaseModel):
    key: str = Field(..., max_length=100)
    value: str
    type: str = Field(default="string", pattern=r"^(string|int|bool|float|json)$")
    description: Optional[str] = Field(default=None, max_length=255)


class SettingResponse(SettingBase):
    id: int
    updated_at: datetime
    updated_by: Optional[int]

    class Config:
        from_attributes = True


class SettingUpdateRequest(BaseModel):
    value: str


class SettingsBatchUpdateRequest(BaseModel):
    settings: dict[str, str]


class PublicSettingsResponse(BaseModel):
    portal_name: str
    coin_system_enabled: bool
    maintenance_mode: bool
    voucher_durations: List[int]


# ──────────────────────────────
# Dashboard Schemas
# ──────────────────────────────
class DashboardStats(BaseModel):
    active_sessions: int
    total_vouchers: int
    used_vouchers_today: int
    expired_sessions_today: int
    total_users: int
    system_status: str
    uptime_minutes: int


class ActivityItem(BaseModel):
    id: int
    level: str
    category: str
    message: str
    created_at: datetime


class UsageDataPoint(BaseModel):
    hour: str
    sessions: int
    data_usage_mb: float


# ──────────────────────────────
# Log Schemas
# ──────────────────────────────
class LogCreateRequest(BaseModel):
    level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")
    category: str = Field(..., max_length=50)
    message: str
    details: Optional[str] = None


class LogResponse(BaseModel):
    id: int
    level: str
    category: str
    message: str
    details: Optional[str]
    created_at: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    logs: List[LogResponse]
    total: int


# ──────────────────────────────
# Coin System Schemas
# ──────────────────────────────
class CoinStatusResponse(BaseModel):
    enabled: bool
    price_per_minute: Optional[float] = None
    currency: Optional[str] = None


class CoinPaymentRequest(BaseModel):
    mac_address: str = Field(..., max_length=17)
    amount: float = Field(..., gt=0)
    minutes: int = Field(..., gt=0)
