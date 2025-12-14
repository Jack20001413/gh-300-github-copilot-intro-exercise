"""
Configuration module for OAuth settings
"""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Settings:
    """Application settings from environment variables"""
    
    # Secret keys
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "dev-session-secret-change-in-production")
    
    def __init__(self):
        # Warn if using default secrets in production
        if self.SECRET_KEY == "dev-secret-key-change-in-production":
            logger.warning("Using default SECRET_KEY! Change this in production!")
        if self.SESSION_SECRET == "dev-session-secret-change-in-production":
            logger.warning("Using default SESSION_SECRET! Change this in production!")
    
    # OAuth settings
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    # OAuth endpoints (GitHub by default)
    OAUTH_AUTHORIZE_URL: str = os.getenv("OAUTH_AUTHORIZE_URL", "https://github.com/login/oauth/authorize")
    OAUTH_TOKEN_URL: str = os.getenv("OAUTH_TOKEN_URL", "https://github.com/login/oauth/access_token")
    OAUTH_USERINFO_URL: str = os.getenv("OAUTH_USERINFO_URL", "https://api.github.com/user")
    
    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Application URL
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    
    # Algorithm for JWT
    ALGORITHM: str = "HS256"
    
    # Security settings
    # Set to True in production (requires HTTPS)
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"

settings = Settings()
