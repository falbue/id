import hashlib
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app import config as settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> tuple[str, str]:
    raw_token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(tz=UTC)
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
