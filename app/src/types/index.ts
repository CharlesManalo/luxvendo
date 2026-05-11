export interface Admin {
  id: number;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Voucher {
  id: number;
  code: string;
  duration_minutes: number;
  status: 'active' | 'used' | 'expired' | 'disabled';
  created_at: string;
  used_at: string | null;
  expires_at: string | null;
  created_by: number | null;
  used_by_mac: string | null;
  used_by_ip: string | null;
}

export interface Session {
  id: number;
  voucher_id: number;
  mac_address: string;
  ip_address: string;
  device_name: string | null;
  login_time: string;
  expiry_time: string;
  last_activity: string;
  status: 'active' | 'expired' | 'terminated' | 'paused';
  data_usage_mb: number;
  is_paused: boolean;
  paused_at: string | null;
  paused_duration: number;
  remaining_minutes?: number;
  voucher_code?: string;
}

export interface User {
  id: number;
  mac_address: string;
  ip_address: string;
  device_name: string | null;
  first_seen: string;
  last_seen: string;
  total_sessions: number;
  total_time_used: number;
  is_blacklisted: boolean;
  notes: string | null;
}

export interface Setting {
  id: number;
  key: string;
  value: string;
  type: 'string' | 'int' | 'bool' | 'json';
  description: string | null;
  updated_at: string;
  updated_by: number | null;
}

export interface LogEntry {
  id: number;
  level: 'debug' | 'info' | 'warning' | 'error';
  category: string;
  message: string;
  details: string | null;
  created_at: string;
  ip_address: string | null;
}

export interface DashboardStats {
  active_sessions: number;
  total_vouchers: number;
  available_vouchers: number;
  used_today: number;
  expired_sessions_today: number;
  total_users: number;
  system_status: 'online' | 'maintenance' | 'offline';
  timestamp: string;
}

export interface ActivityItem {
  id: number;
  level: string;
  category: string;
  message: string;
  created_at: string;
}

export interface UsageDataPoint {
  hour: string;
  sessions: number;
  data_usage_mb: number;
}

export interface CoinStatus {
  enabled: boolean;
  price_per_minute: number | null;
  currency: string | null;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success?: boolean;
  message?: string;
}
