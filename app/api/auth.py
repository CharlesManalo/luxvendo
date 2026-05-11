"""Authentication utilities - password hashing and session management."""
import uuid
import datetime
from typing import Optional, Dict
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory session store: token -> {admin_id, created_at}
sessions: Dict[str, dict] = {}


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_session(admin_id: int) -> str:
    """Create a new session token and store it."""
    token = str(uuid.uuid4())
    sessions[token] = {
        "admin_id": admin_id,
        "created_at": datetime.datetime.utcnow(),
    }
    return token


def get_session(token: str) -> Optional[dict]:
    """Get session data if token is valid."""
    session = sessions.get(token)
    if not session:
        return None
    # Check expiry (24 hours)
    age = datetime.datetime.utcnow() - session["created_at"]
    if age.total_seconds() > 86400:
        del sessions[token]
        return None
    return session


def delete_session(token: str) -> bool:
    """Delete a session."""
    if token in sessions:
        del sessions[token]
        return True
    return False


def cleanup_expired_sessions():
    """Remove expired sessions from memory."""
    now = datetime.datetime.utcnow()
    expired = [
        token for token, data in sessions.items()
        if (now - data["created_at"]).total_seconds() > 86400
    ]
    for token in expired:
        del sessions[token]
