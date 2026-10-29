from fastapi import Depends, HTTPException, status, Cookie, Request
from sqlmodel import Session, select
from app.database import get_session
from app.models.user import Users
from app.core.security import decode_token


def get_current_user_secure(
    request: Request,
    session: Session = Depends(get_session),
    access_token_cookie: str | None = Cookie(None, alias="access_token"),
) -> Users:

    token = None

    # 1. Приоритет: Заголовок Authorization (Bearer scheme)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Фоллбэк: Кука access_token (для удобства фронтенда и тестов)
    if not token and access_token_cookie:
        token = access_token_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен авторизации не предоставлен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token, expected_type="access")
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid payload structure")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истекший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.exec(select(Users).where(Users.id == user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден в системе",
        )

    return user
