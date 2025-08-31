# 사용자 저장소 레이어
# - 데이터 접근(조회/생성)만 담당 (서비스 로직 분리)

from typing import Optional
from beanie import PydanticObjectId
from pydantic import EmailStr
from ..models.user import User

class UserRepository:
    async def get_by_email(self, email: EmailStr) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def create(self, email: EmailStr, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        return await user.insert()

    async def get(self, user_id: str) -> Optional[User]:
        return await User.get(PydanticObjectId(user_id))
