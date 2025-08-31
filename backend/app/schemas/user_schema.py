# 요청/응답 스키마 정의 (Pydantic 모델)

from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserPublic(BaseModel):
    id: str
    email: EmailStr
