# 보안 유닛 테스트 (DB 의존성 없음)
from app.core.security import get_password_hash, verify_password, create_access_token
import jwt
from app.core.config import settings

def test_password_hash_and_verify():
    pw = "S3cure!"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)

def test_create_access_token():
    token = create_access_token("user123")
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == "user123"
    assert decoded["type"] == "access"
