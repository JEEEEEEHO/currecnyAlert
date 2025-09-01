# 인증 라우터
# - 회원가입: POST /api/v1/auth/register
# - 로그인: POST /api/v1/auth/login

from fastapi import APIRouter, Depends
from beanie import PydanticObjectId

from ...schemas.user_schema import UserCreate, TokenPair, UserPublic
from ...services.auth_service import AuthService, get_auth_service
from ...core.config import settings
from ...core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic, summary="회원가입 (이메일 중복 체크 포함)")
async def register(payload: UserCreate, service: AuthService = Depends(get_auth_service)):
    user = await service.register(payload.email, payload.password)
    return {"id": str(user.id), "email": user.email}

@router.post("/login", response_model=TokenPair, summary="로그인 (JWT Access/Refresh 토큰 발급)")
async def login(payload: UserCreate, service: AuthService = Depends(get_auth_service)):
    # 간단히 동일 스키마 사용 (email/password)
    tokens = await service.login(payload.email, payload.password)
    return tokens
