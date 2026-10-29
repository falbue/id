import hashlib
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app import config as settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def hash_refresh_token(token: str) -> str:
    """Хеширует рефреш-токен для безопасного хранения в БД."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token_data(user_id: int) -> tuple[str, str]:
    """Создает сырой токен для клиента и хеш для БД."""
    raw_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.utcnow()
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return raw_token, hash_refresh_token(raw_token)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise JWTError("Неверный тип токена")
        return payload
    except JWTError:
        raise ValueError("Недействительный или просроченный токен")
