"""
JWT Authentication Module

This module handles JWT (JSON Web Token) creation and validation.
JWT tokens are signed, self-contained tokens that include user information.

WHY JWT?
- Stateless: No need to store tokens on server
- Secure: Cryptographically signed, can't be tampered with
- Self-contained: Token includes user info (no database lookup needed)
- Standard: Widely used, well-supported

TOKEN STRUCTURE:
A JWT has 3 parts separated by dots:
1. Header (algorithm and token type)
2. Payload (user data: user_id, username, etc.)
3. Signature (ensures token hasn't been tampered with)

Example: header.payload.signature

TOKEN LIFETIME:
- Tokens expire after 7 days (configurable)
- Frontend should refresh tokens before expiration
- Expired tokens are automatically rejected
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

# ============================================================================
# JWT CONFIGURATION
# ============================================================================

# Secret key for signing tokens
# In production, use a strong random key from environment variable
# For development, this is fine, but CHANGE IT in production!
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fadmann-secret-key-change-in-production-2024")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))


# ============================================================================
# TOKEN CREATION
# ============================================================================

def create_access_token(user_id: int, username: str) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: The user's ID
        username: The user's username
    
    Returns:
        A signed JWT token string
    
    How it works:
    1. Create payload with user info and expiration time
    2. Sign the token with our secret key
    3. Return the token as a string
    
    The token includes:
    - user_id: To identify the user
    - username: For quick access
    - exp: Expiration timestamp
    - iat: Issued at timestamp
    """
    # Calculate expiration time
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    # Create payload (the data inside the token)
    payload = {
        "sub": str(user_id),  # "sub" (subject) is standard JWT field for user ID
        "username": username,
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow()  # Issued at time
    }
    
    # Encode and sign the token
    # This creates: header.payload.signature
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


# ============================================================================
# TOKEN VALIDATION
# ============================================================================

def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string to verify
    
    Returns:
        Dictionary with token payload if valid, None if invalid
    
    What it checks:
    1. Token signature is valid (hasn't been tampered with)
    2. Token hasn't expired
    3. Token format is correct
    
    Raises:
        JWTError: If token is invalid, expired, or malformed
    """
    try:
        # Decode and verify the token
        # This automatically checks:
        # - Signature is valid
        # - Token hasn't expired
        # - Token format is correct
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return payload
    
    except JWTError:
        # Token is invalid, expired, or malformed
        return None


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Get user object from JWT token.
    
    Args:
        token: The JWT token string
        db: Database session
    
    Returns:
        User object if token is valid, None otherwise
    
    Flow:
    1. Verify token signature and expiration
    2. Extract user_id from token payload
    3. Query database for user
    4. Return user object
    """
    # Verify token
    payload = verify_token(token)
    if not payload:
        return None
    
    # Extract user_id from token
    user_id = int(payload.get("sub"))
    if not user_id:
        return None
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    return user


# ============================================================================
# FASTAPI DEPENDENCY
# ============================================================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    This function is used as a dependency in route handlers.
    FastAPI automatically calls it and injects the result.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            # user is automatically available here
            return {"user_id": user.id}
    
    Args:
        authorization: Authorization header value (e.g., "Bearer token123")
        db: Database session (injected by FastAPI)
    
    Returns:
        User object if authenticated
    
    Raises:
        HTTPException 401: If token is invalid or missing
    
    How it works:
    1. FastAPI automatically extracts Authorization header
    2. We check if it starts with "Bearer "
    3. Extract the token
    4. Verify token signature and expiration
    5. Extract user_id from token
    6. Query database for user
    7. Return user object
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token
    token = authorization.replace("Bearer ", "").strip()
    
    # Get user from token
    user = get_user_from_token(token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
