from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    existing = await session.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        phone=payload.phone,
        role=UserRole.citizen,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenOut:
    res = await session.execute(select(User).where(User.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        subject=user.email,
        role=user.role.value,
        secret=settings.jwt_secret,
        expire_minutes=settings.access_token_expire_minutes,
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value)


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    if "name" in payload and payload["name"] is not None:
        user.name = payload["name"].strip()
    if "phone" in payload and payload["phone"] is not None:
        user.phone = payload["phone"].strip()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserOut(id=user.id, email=user.email, name=user.name, role=user.role.value)

