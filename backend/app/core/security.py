# 보안/인증 유틸리티
# - 비밀번호 해싱/검증
# - JWT 토큰 생성/검증
# - 현재 사용자 가져오기(의존성)

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt

from .config import settings
from ..models.user import User
from beanie import PydanticObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(subject: dict, expires_delta: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "exp": now + expires_delta,
        "iat": now,
        "nbf": now,
        **subject,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def create_access_token(user_id: str) -> str:
    return create_token({"sub": str(user_id), "type": "access"}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(user_id: str) -> str:
    return create_token({"sub": str(user_id), "type": "refresh"}, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # JWT 토큰 파싱 및 사용자 조회
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise credentials_exception

    return user
