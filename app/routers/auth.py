from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from app import config as settings
from app.models.token import RefreshTokens
from app.models.user import Users
from app.schemas.token import AccessTokenResponse, TokenPair
from app.schemas.user import UserLogin, UserRegister, UserResponse
from app.services.database import get_async_session
from app.services.security import (
    create_access_token,
    create_refresh_token_data,
    decode_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)

router = APIRouter()


def set_refresh_cookie(response: Response, refresh_token: str):
    """Устанавливает refresh токен в http-only cookie"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,  # True в продакшене с HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=settings.COOKIE_DOMAIN if hasattr(settings, "COOKIE_DOMAIN") else None,
    )


def create_and_store_refresh_token(
    session: Session, user_id: int, request: Request
) -> str:
    """Создает и сохраняет refresh токен в БД, возвращает (raw_token, access_token)"""
    raw_refresh_token, refresh_token_hash = create_refresh_token_data(user_id)

    if request.client is None or request.client.host is None:
        host = "0.0.0.0"
    else:
        host = request.client.host

    device_info = f"IP: {host}, UA: {request.headers.get('user-agent', 'Unknown')}"
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshTokens(
        user_id=user_id,
        token_hash=refresh_token_hash,
        device_info=device_info,
        expires_at=expires_at,
    )
    session.add(db_token)
    session.commit()

    return raw_refresh_token


@router.post(
    "/registration", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    user_in: UserRegister,
    request: Request,
    response: Response,
    session: Session = Depends(get_async_session),
):
    """Регистрация пользователя с выдачей токенов"""
    if user_in.email:
        existing = session.exec(
            select(Users).where(Users.email == user_in.email)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    if user_in.phone:
        existing = session.exec(
            select(Users).where(Users.phone == user_in.phone)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")

    db_user = Users(
        email=user_in.email,
        phone=user_in.phone,
        password_hash=get_password_hash(user_in.password),
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    raw_refresh_token = create_and_store_refresh_token(session, db_user.id, request)

    set_refresh_cookie(response, raw_refresh_token)

    return db_user


@router.post("/login", response_model=AccessTokenResponse)
def login(
    user_in: UserLogin,
    request: Request,
    response: Response,
    session: Session = Depends(get_async_session),
):
    """Вход пользователя с выдачей токенов"""
    statement = select(Users)
    if user_in.email:
        statement = statement.where(Users.email == user_in.email)
    else:
        statement = statement.where(Users.phone == user_in.phone)

    user = session.exec(statement).first()

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    user.last_login = datetime.utcnow()
    session.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    raw_refresh_token = create_and_store_refresh_token(session, user.id, request)

    set_refresh_cookie(response, raw_refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_async_session),
):
    """Обновление access токена с использованием refresh токена из куки"""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Рефреш-токен не найден")

    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub"))  # type: ignore
    except ValueError:
        raise HTTPException(status_code=401, detail="Недействительный рефреш-токен")

    token_hash = hash_refresh_token(refresh_token)

    db_token = session.exec(
        select(RefreshTokens).where(
            RefreshTokens.token_hash == token_hash,
            RefreshTokens.user_id == user_id,
            RefreshTokens.is_revoked == False,
        )
    ).first()

    if not db_token:
        raise HTTPException(status_code=401, detail="Токен отозван или не найден")

    if db_token.expires_at < datetime.utcnow():
        db_token.is_revoked = True
        session.commit()
        raise HTTPException(status_code=401, detail="Срок действия токена истек")

    db_token.is_revoked = True
    new_access_token = create_access_token(data={"sub": str(user_id)})
    new_raw_refresh, new_refresh_hash = create_refresh_token_data(user_id)

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_db_token = RefreshTokens(
        user_id=user_id,
        token_hash=new_refresh_hash,
        device_info=db_token.device_info,
        expires_at=expires_at,
    )
    session.add(new_db_token)
    session.commit()

    set_refresh_cookie(response, new_raw_refresh)
    return AccessTokenResponse(access_token=new_access_token)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_async_session),
):
    """
    Logout endpoint - отзывает токен и удаляет куку
    status_code=204 означает "No Content" - пустой ответ
    """
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        db_token = session.exec(
            select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
        ).first()

        if db_token:
            db_token.is_revoked = True
            session.commit()

    response.delete_cookie(
        key="refresh_token",
        path="/",  # Должен совпадать с path при установке
    )

    return None
