# 인증 서비스 레이어
# - 이메일 중복 체크, 회원가입
# - 로그인 (비밀번호 검증, JWT 토큰 발급)

from fastapi import HTTPException, status, Depends
from pydantic import EmailStr
from typing import Union
from ..repositories.user_repository import UserRepository
from ..core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from ..schemas.user_schema import TokenPair

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, email: EmailStr, password: str):
        existing = await self.repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        hashed = get_password_hash(password)
        user = await self.repo.create(email, hashed)
        return user

    async def login(self, email: EmailStr, password: str) -> TokenPair:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        return TokenPair(access_token=access, refresh_token=refresh)


def get_auth_service(repo: UserRepository = Depends(UserRepository)) -> AuthService:
    return AuthService(repo)
