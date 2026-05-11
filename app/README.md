# WiFi Voucher System

A production-ready voucher-based WiFi gateway backend and admin system for Ubuntu Linux. The server acts as the central controller handling voucher authentication, session management, expiry tracking, and administrative control. External routers operate in AP mode only -- all intelligence lives on the backend.

## Features

### Voucher System
- Generate secure random voucher codes (XXXX-XXXX format)
- Set duration per voucher: 30 min, 1 hour, 3 hours, 1 day
- Voucher statuses: active, used, expired, disabled
- Bulk generation (up to 100 at once)
- Export vouchers to CSV

### Session Management
- Track active users with MAC address, IP address, login time, expiry time
- Auto-expire sessions (background task checks every 60 seconds)
- Manual kick, pause, resume, and extend sessions
- Remaining time calculation

### Admin Dashboard
- Dark modern responsive design
- Real-time statistics (active sessions, vouchers, users)
- Active sessions table with quick actions
- Recent activity feed
- Mobile responsive layout

### Coin System
- **Disabled by default** as required
- Admin toggle to enable/disable
- Configurable price per minute and currency
- Pricing table preview for ESP32 hardware integration
- Future-ready for coin acceptor hardware

### Security
- Session-based authentication with HTTP-only cookies
- API key authentication for router endpoints
- Bcrypt password hashing
- Rate limiting ready
- MAC + IP tracking for spoof prevention

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite, Uvicorn
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui
- **Auth:** Passlib (bcrypt), in-memory session store

## Quick Start

### Option 1: Development Mode

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node dependencies
npm install

# 3. Start the backend
python3 start.sh

# 4. In another terminal, start the frontend dev server
npm run dev
```

### Option 2: Production Install (Ubuntu)

```bash
# Run the automated installer as root
sudo bash install.sh

# Start the service
sudo systemctl start wifi-voucher-system

# Check status
sudo systemctl status wifi-voucher-system

# View logs
sudo journalctl -u wifi-voucher-system -f
```

### Option 3: Manual Production Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip sqlite3

# Install Python packages
pip3 install -r requirements.txt

# Build frontend
npm install
npm run build

# Create database directory
mkdir -p db

# Start server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Default Login

- **Username:** `admin`
- **Password:** `admin123`

**Important:** Change the default password after first login via Settings > Security.

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Admin login (returns session cookie) |
| POST | `/api/auth/logout` | Clear session |
| GET | `/api/auth/me` | Get current admin info |
| POST | `/api/auth/setup` | First-run admin creation |
| GET | `/api/auth/check-setup` | Check if setup needed |

### Vouchers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vouchers` | List vouchers (with filters) |
| POST | `/api/vouchers/generate` | Generate single voucher |
| POST | `/api/vouchers/bulk-generate` | Bulk generate vouchers |
| GET | `/api/vouchers/{id}` | Get voucher details |
| POST | `/api/vouchers/{id}/disable` | Disable a voucher |
| DELETE | `/api/vouchers/{id}` | Delete a voucher |
| POST | `/api/vouchers/validate` | Validate voucher (public, API key) |
| POST | `/api/vouchers/activate` | Activate voucher (public, API key) |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List active sessions |
| GET | `/api/sessions/history` | Session history |
| POST | `/api/sessions/{id}/terminate` | Kick user |
| POST | `/api/sessions/{id}/pause` | Pause session |
| POST | `/api/sessions/{id}/resume` | Resume session |
| POST | `/api/sessions/{id}/extend` | Extend session time |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users |
| GET | `/api/users/{id}` | User details with history |
| POST | `/api/users/{id}/blacklist` | Block MAC |
| POST | `/api/users/{id}/unblacklist` | Unblock MAC |
| DELETE | `/api/users/{id}` | Delete user |

### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get all settings |
| POST | `/api/settings` | Update settings (batch) |
| GET | `/api/settings/public/config` | Public config (API key) |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Overview statistics |
| GET | `/api/dashboard/activity` | Recent activity |
| GET | `/api/dashboard/usage` | Usage chart data |

### Coin System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/coin/status` | Check coin system status |
| GET | `/api/coin/price` | Get pricing table |
| POST | `/api/coin/payment` | Record coin payment |

## Database Schema

### Tables

- **admins** - Admin accounts
- **vouchers** - Voucher codes with status and usage tracking
- **sessions** - Active WiFi sessions with expiry
- **users** - Unique devices by MAC address
- **settings** - System configuration (key-value store)
- **logs** - System activity logs

See `api/models.py` for full schema definitions.

## Configuration

All settings are managed through the admin panel at `/settings` or via the API.

### Default Settings
| Key | Default | Description |
|-----|---------|-------------|
| `portal_name` | Free WiFi | Portal display name |
| `session_timeout` | 1440 | Default timeout (minutes) |
| `max_devices` | 50 | Max concurrent devices |
| `coin_system_enabled` | false | Coin system toggle |
| `maintenance_mode` | false | Maintenance mode |
| `voucher_durations` | [30,60,180,1440] | Available durations |
| `coin_price_per_minute` | 0.5 | Coin pricing |
| `coin_currency` | USD | Currency |

## Captive Portal Integration

The system is designed for future captive portal integration:

1. Router (AP mode) redirects user to captive portal
2. Portal calls `POST /api/vouchers/validate` with API key to check code
3. Portal calls `POST /api/vouchers/activate` with MAC/IP to create session
4. Router allows traffic for the MAC address

### Public Endpoints (API Key Auth)
- `POST /api/vouchers/validate` - Check voucher validity
- `POST /api/vouchers/activate` - Activate voucher and create session
- `GET /api/settings/public/config` - Get portal settings

Send API key in header: `X-API-Key: your-api-key`

## ESP32 Hardware Integration

For coin acceptor hardware:

1. Enable coin system in Settings > Coin System
2. ESP32 reads coin insertions
3. ESP32 calls `POST /api/coin/payment` with MAC, amount, minutes
4. Backend returns a voucher code
5. ESP32 displays voucher to user

## Project Structure

```
.
|-- api/                    # FastAPI backend
|   |-- main.py             # Application entry point
|   |-- config.py           # Configuration
|   |-- database.py         # SQLAlchemy setup
|   |-- models.py           # Database models
|   |-- schemas.py          # Pydantic schemas
|   |-- auth.py             # Auth utilities
|   |-- middleware.py       # Auth middleware
|   |-- seeds.py            # Initial data seeding
|   |-- routers/
|   |   |-- auth.py         # Authentication
|   |   |-- vouchers.py     # Voucher management
|   |   |-- sessions.py     # Session management
|   |   |-- users.py        # User management
|   |   |-- settings.py     # System settings
|   |   |-- dashboard.py    # Statistics
|   |   |-- logs.py         # System logs
|   |   |-- coin.py         # Coin system
|-- src/                    # React frontend
|   |-- main.tsx            # React entry
|   |-- App.tsx             # Routes
|   |-- index.css           # Global styles
|   |-- context/
|   |   |-- AuthContext.tsx  # Auth state
|   |-- hooks/
|   |   |-- useApi.ts       # API client
|   |   |-- usePolling.ts   # Real-time polling
|   |-- pages/
|   |   |-- Login.tsx       # Login page
|   |   |-- Dashboard.tsx   # Main dashboard
|   |   |-- Vouchers.tsx    # Voucher management
|   |   |-- Users.tsx       # User management
|   |   |-- Settings.tsx    # Settings panel
|   |-- components/
|   |   |-- Layout.tsx      # App layout
|   |   |-- Sidebar.tsx     # Navigation
|   |   |-- StatCard.tsx    # Stat card
|   |   |-- StatusBadge.tsx # Status badge
|   |-- types/
|   |   |-- index.ts        # TypeScript types
|-- db/                     # SQLite database
|-- install.sh              # Ubuntu installer
|-- start.sh                # Development startup
|-- requirements.txt        # Python dependencies
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | sqlite+aiosqlite:///db/wifi_system.db | Database path |
| `SECRET_KEY` | auto-generated | Session signing key |
| `API_KEY` | auto-generated | Router API key |
| `APP_NAME` | WiFi Voucher System | App name |
| `DEBUG` | false | Debug mode |
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Bind address |
| `CORS_ORIGINS` | * | Allowed CORS origins |

## License

MIT
