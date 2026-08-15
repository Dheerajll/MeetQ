"""
Authentication endpoints.

Google OAuth flow:
1. GET /auth/google         → Redirects user to Google consent screen
2. GET /auth/google/callback → Google sends back auth code,
                               we exchange it for user info,
                               create/find user in DB,
                               return JWT

LMA Token Management:
3. POST /auth/lma-token     → Generate device token (requires JWT)
4. GET  /auth/lma/verify    → Verify device token (used by LMA CLI)
"""
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, generate_lma_token
from app.models.user import User
from app.models.lma_token import LMAToken
from app.schemas.lma_token import LMATokenCreate, LMATokenResponse
from app.api.deps import get_current_user, get_current_lma

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = "openid email profile"


# ============================================================
# GOOGLE OAUTH
# ============================================================

@router.get("/google")
async def google_login():
    """
    Step 1: Redirect the user to Google's consent screen.
    The frontend should redirect the browser to this URL.
    """
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    })
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2: Google redirects back here with an authorization code.
    We exchange the code for tokens, fetch user info,
    create/find the user in our DB, and return a JWT.
    """
    # --- Exchange auth code for access token ---
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code",
        )

    token_data = token_response.json()
    google_access_token = token_data.get("access_token")

    if not google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from Google",
        )

    # --- Fetch user info from Google ---
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {google_access_token}"
            },
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user info from Google",
        )

    userinfo = userinfo_response.json()
    google_id = userinfo.get("id")
    email = userinfo.get("email")
    name = userinfo.get("name", "Unknown")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete user info from Google",
        )

    # --- Find or create user in our database ---
    stmt = select(User).where(User.google_id == google_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✓ New user created: {email}")
    else:
        print(f"✓ Existing user logged in: {email}")

    # --- Generate our own JWT ---
    jwt_token = create_access_token(subject=user.email)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
    }


# ============================================================
# LMA TOKEN MANAGEMENT
# ============================================================

@router.post("/lma-token", response_model=LMATokenResponse)
async def create_lma_token(
    payload: LMATokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new LMA device token for the logged-in user.
    The token is returned ONLY ONCE. Store it safely!
    """
    token_string = generate_lma_token()

    lma_token = LMAToken(
        user_id=current_user.id,
        token=token_string,
        device_name=payload.device_name,
        is_active=True,
    )
    db.add(lma_token)
    await db.commit()
    await db.refresh(lma_token)

    return lma_token


@router.get("/lma/verify")
async def verify_lma_token(
    current_lma: LMAToken = Depends(get_current_lma),
):
    """
    Verifies an LMA token.
    This is the exact endpoint the `lma config verify` CLI command calls.
    """
    return {
        "status": "valid",
        "user_email": current_lma.user.email,
        "device_name": current_lma.device_name,
    }