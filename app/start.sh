#!/bin/bash
# WiFi Voucher System - Startup Script
# Usage: ./start.sh [port]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${1:-8000}
HOST=${HOST:-0.0.0.0}

echo "=========================================="
echo "  WiFi Voucher System"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required but not installed."
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import fastapi, sqlalchemy, pydantic, passlib" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
}

# Create database directory
mkdir -p db

echo ""
echo "Starting server on http://${HOST}:${PORT}"
echo "Admin Panel: http://${HOST}:${PORT}"
echo "API Docs: http://${HOST}:${PORT}/docs"
echo ""
echo "Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

# Start the server
python3 -m uvicorn api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload
