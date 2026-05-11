"""FastAPI application entry point."""
import asyncio
import datetime
from contextlib import asynccontextmanager

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from api.config import CORS_ORIGINS, APP_NAME, DEBUG
from api.database import engine, Base, AsyncSessionLocal
from api.auth import cleanup_expired_sessions
from api.seeds import seed_database
from api.auth import sessions as session_store
from api.routers import (
    auth,
    vouchers,
    sessions,
    users,
    settings,
    dashboard,
    logs,
    coin,
)


async def check_expired_sessions():
    """Background task: check and mark expired sessions."""
    from sqlalchemy import select, and_
    from api.models import Session as SessionModel, Voucher
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every 60 seconds
            
            async with AsyncSessionLocal() as db:
                now = datetime.datetime.utcnow()
                
                # Find expired sessions
                result = await db.execute(
                    select(SessionModel).where(
                        and_(
                            SessionModel.status == "active",
                            SessionModel.expiry_time <= now,
                            SessionModel.is_paused == False,
                        )
                    )
                )
                expired_sessions = result.scalars().all()
                
                for session in expired_sessions:
                    session.status = "expired"
                    
                    # Update voucher
                    if session.voucher_id:
                        voucher_result = await db.execute(
                            select(Voucher).where(Voucher.id == session.voucher_id)
                        )
                        voucher = voucher_result.scalar_one_or_none()
                        if voucher:
                            voucher.status = "expired"
                
                if expired_sessions:
                    await db.commit()
                    
                # Clean up old sessions from memory
                cleanup_expired_sessions()
                
        except asyncio.CancelledError:
            break
        except Exception:
            # Don't crash the background task
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed data
    async with AsyncSessionLocal() as db:
        await seed_database(db)
    
    # Start background task
    expiry_task = asyncio.create_task(check_expired_sessions())
    
    yield
    
    # Shutdown
    expiry_task.cancel()
    try:
        await expiry_task
    except asyncio.CancelledError:
        pass
    
    await engine.dispose()


app = FastAPI(
    title=APP_NAME,
    description="Voucher-based WiFi gateway backend with admin panel",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc) if DEBUG else "Something went wrong"},
    )


# ─── API Routes ───

app.include_router(auth.router, prefix="/api")
app.include_router(vouchers.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(coin.router, prefix="/api")


# ─── Health Check ───

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": "1.0.0",
    }


# ─── Static Files (Frontend) ───

DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
if DIST_DIR.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

@app.get("/")
async def serve_index():
    """Serve the React SPA or API info."""
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": f"{APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "note": "Frontend not built. Run 'npm run build' to serve the admin panel.",
    }

# Catch-all for SPA routing (must be after API routes)
@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve index.html for all non-API routes (SPA support)."""
    # Skip API routes
    if path.startswith("api/") or path == "docs" or path == "openapi.json":
        return {"detail": "Not found"}
    
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"detail": "Not found"}


if __name__ == "__main__":
    import uvicorn
    from api.config import HOST, PORT
    
    uvicorn.run(
        "api.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
