# 알림 설정 모델
# - 특정 사용자가 알림을 활성화했는지 관리

from datetime import datetime
from beanie import Document, Link
from pydantic import Field

from .user import User

class NotificationSetting(Document):
    user: Link[User]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "notification_settings"
