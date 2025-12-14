"""
OAuth 2.0 authentication module with PKCE support
"""
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response
from jose import jwt, JWTError
import httpx
from src.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# In-memory storage for sessions and tokens (in production, use Redis or database)
# Note: For production deployments, replace with Redis or database backend
# to support multiple server instances and prevent memory leaks
sessions: Dict[str, Dict[str, Any]] = {}
refresh_tokens: Dict[str, Dict[str, Any]] = {}


def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    current_time = datetime.now(timezone.utc)
    expired_sessions = [
        token for token, data in sessions.items()
        if data.get("expires", current_time) < current_time
    ]
    for token in expired_sessions:
        del sessions[token]
    
    expired_refresh = [
        token for token, data in refresh_tokens.items()
        if data.get("expires", current_time) < current_time
    ]
    for token in expired_refresh:
        del refresh_tokens[token]


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def generate_state():
    """Generate state parameter for CSRF protection"""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str):
    """Create refresh token"""
    token = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_tokens[token] = {
        "user_id": user_id,
        "expires": expire
    }
    return token


def verify_access_token(token: str) -> Optional[dict]:
    """Verify and decode access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return user_id"""
    token_data = refresh_tokens.get(token)
    if not token_data:
        return None
    
    if datetime.now(timezone.utc) > token_data["expires"]:
        del refresh_tokens[token]
        return None
    
    return token_data["user_id"]


def revoke_refresh_token(token: str):
    """Revoke a refresh token"""
    if token in refresh_tokens:
        del refresh_tokens[token]


async def get_oauth_user_info(access_token: str) -> Optional[dict]:
    """Fetch user information from OAuth provider"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                settings.OAUTH_USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            if response.status_code == 200:
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error fetching user info: {e}")
    return None


async def exchange_code_for_token(code: str, code_verifier: str) -> Optional[dict]:
    """Exchange authorization code for access token"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.OAUTH_TOKEN_URL,
                headers={
                    "Accept": "application/json"
                },
                data={
                    "client_id": settings.OAUTH_CLIENT_ID,
                    "client_secret": settings.OAUTH_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.OAUTH_REDIRECT_URI,
                    "code_verifier": code_verifier
                }
            )
            if response.status_code == 200:
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Error exchanging code for token: {e}")
    return None


def get_session_user(request: Request) -> Optional[dict]:
    """Get user from session cookie"""
    # Periodically clean up expired sessions
    cleanup_expired_sessions()
    
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    
    session = sessions.get(session_token)
    if not session:
        return None
    
    # Check if session has expired
    if datetime.now(timezone.utc) > session.get("expires", datetime.now(timezone.utc)):
        del sessions[session_token]
        return None
    
    return session.get("user")


def create_session(user: dict, response: Response):
    """Create a new session for user"""
    session_token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    sessions[session_token] = {
        "user": user,
        "expires": expires
    }
    
    # Set httpOnly cookie for session
    # Note: secure flag should be True in production with HTTPS
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Create refresh token and set it as httpOnly cookie
    refresh_token = create_refresh_token(user["email"])
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )


def clear_session(request: Request, response: Response):
    """Clear user session"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in sessions:
        del sessions[session_token]
    
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        revoke_refresh_token(refresh_token)
    
    response.delete_cookie(key="session_token")
    response.delete_cookie(key="refresh_token")
