# User 도메인 모델 (Beanie Document)
# - 이메일, 비밀번호 해시, 생성일
# - 이메일은 unique 인덱스

from datetime import datetime
from beanie import Document, Indexed
from pydantic import EmailStr, Field

class User(Document):
    email: Indexed(EmailStr, unique=True)  # 중복 방지 인덱스
    hashed_password: str = Field(repr=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"  # 컬렉션명
