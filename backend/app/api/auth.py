from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token, verify_clerk_token
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse, UserResponse, UserUpdate
from app.core.config import settings
import uuid
import re
import time
import asyncio
import httpx

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# ── Clerk profile lookup (session JWTs only carry `sub`, not email/name) ──────
_CLERK_PROFILE_CACHE: dict = {}
_CLERK_PROFILE_CACHE_TTL = 300
_CLERK_PROFILE_LOCK = asyncio.Lock()


async def _fetch_clerk_profile(user_id: str) -> dict:
    """Fetch a Clerk user profile from the Backend API, with a short TTL cache."""
    now = time.monotonic()
    cached = _CLERK_PROFILE_CACHE.get(user_id)
    if cached and now - cached[0] < _CLERK_PROFILE_CACHE_TTL:
        return cached[1]

    secret_key = settings.CLERK_SECRET_KEY
    if not secret_key:
        raise HTTPException(status_code=401, detail="CLERK_SECRET_KEY not configured")

    async with _CLERK_PROFILE_LOCK:
        cached = _CLERK_PROFILE_CACHE.get(user_id)
        if cached and now - cached[0] < _CLERK_PROFILE_CACHE_TTL:
            return cached[1]
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers={"Authorization": f"Bearer {secret_key}"},
                )
        except httpx.HTTPError:
            raise HTTPException(status_code=401, detail="Could not verify Clerk user")
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Could not verify Clerk user")
        profile = resp.json()
        _CLERK_PROFILE_CACHE[user_id] = (time.monotonic(), profile)
        return profile


async def get_demo_user(db: AsyncSession) -> User:
    """Get or create the shared demo user used when AUTH_BYPASS is enabled."""
    result = await db.execute(select(User).where(User.username == "demo"))
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(
        email="demo@academia.ai",
        username="demo",
        full_name="Demo Student",
        hashed_password=get_password_hash("demo"),
        role=UserRole.STUDENT,
        university="Academia University",
        course="Computer Science",
        semester=3,
        education_level="Undergraduate",
        occupation="Student",
        domain="Computer Science",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _unique_username(db: AsyncSession, base: str) -> str:
    """Return a unique username derived from `base`."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", base)[:80] or "student"
    candidate = clean
    for i in range(1, 100):
        result = await db.execute(select(User).where(User.username == candidate))
        if not result.scalar_one_or_none():
            return candidate
        candidate = f"{clean}_{i}"
    return f"{clean}_{uuid.uuid4().hex[:8]}"


async def get_or_create_user_from_clerk(db: AsyncSession, payload: dict) -> User:
    """Find the local user for a verified Clerk token, creating one if needed."""
    user_id = payload.get("sub")
    email = (payload.get("email") or "").strip().lower()
    full_name = payload.get("name") or " ".join(filter(None, [payload.get("first_name"), payload.get("last_name")]))
    avatar_url = payload.get("image") or payload.get("avatar")

    # Clerk session JWTs only include `sub` — resolve profile from the Backend API
    if not email:
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user id")
        profile = await _fetch_clerk_profile(user_id)
        emails = profile.get("email_addresses") or []
        primary = next(
            (e["email_address"] for e in emails if e.get("id") == profile.get("primary_email_address_id")),
            (emails[0].get("email_address", "") if emails else ""),
        )
        email = primary
        full_name = full_name or " ".join(filter(None, [profile.get("first_name"), profile.get("last_name")]))
        avatar_url = avatar_url or profile.get("image_url")

    email = email.strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Token missing email claim")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            await db.commit()
        return user

    full_name = (
        full_name
        or email.split("@")[0]
    )
    user = User(
        email=email,
        username=await _unique_username(db, email.split("@")[0]),
        full_name=full_name,
        hashed_password=get_password_hash(str(uuid.uuid4())),
        role=UserRole.STUDENT,
        avatar_url=avatar_url,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.AUTH_BYPASS:
        return await get_demo_user(db)
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_clerk_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return await get_or_create_user_from_clerk(db, payload)


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(
        (User.email == data.email) | (User.username == data.username)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        university=data.university,
        course=data.course,
        semester=data.semester,
        education_level=data.education_level,
        occupation=data.occupation,
        domain=data.domain,
        learning_mode=data.learning_mode,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(credentials.credentials) if credentials else None
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)