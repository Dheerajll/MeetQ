# Dependency injection utilities
# Provides get_db (database session), get_current_user (auth) dependencies for FastAPI
"""
FastAPI Dependencies.

Handles authentication and database session injection for API routes.
"""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.lma_token import LMAToken

# This tells FastAPI where the login endpoint is (for Swagger UI auth button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates a JWT access token and returns the associated User.
    Used for protecting web dashboard endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decode the JWT
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    # 2. Fetch the user from the database
    # (Assuming subject is the user's email or google_id)
    stmt = select(User).where(User.email == subject)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )

    return user


async def get_current_lma(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> LMAToken:
    """
    Validates an LMA device token and returns the LMAToken object.
    Used for protecting endpoints that the Local Meeting Agent calls.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or revoked LMA token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Fetch the token from the database
    stmt = (
        select(LMAToken)
        .options(selectinload(LMAToken.user))  # Eager load the user relationship
        .where(LMAToken.token == token)
    )
    result = await db.execute(stmt)
    lma_token = result.scalar_one_or_none()

    # 2. Validate token exists and is active
    if lma_token is None or not lma_token.is_active:
        raise credentials_exception
    
    if not lma_token.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is inactive"
        )

    # 3. Update last_used_at timestamp
    lma_token.last_used_at = datetime.now(timezone.utc)
    # Note: The session will be committed automatically by the get_db dependency 
    # if the request finishes successfully.

    return lma_token