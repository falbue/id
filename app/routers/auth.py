from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from app import config as settings
from app.entities.token import AccessTokenResponse, RefreshTokens
from app.entities.user import UserCreate, UserLogin, UserResponse, Users
from app.services.database import AsyncSession, get_async_session
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)

router = APIRouter()
_session_dependency = Depends(get_async_session)


def set_refresh_cookie(response: Response, refresh_token: str):
    """Устанавливает refresh токен в http-only cookie"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=settings.COOKIE_DOMAIN if hasattr(settings, "COOKIE_DOMAIN") else None,
    )


async def create_and_store_refresh_token(
    session: AsyncSession, user_id: int, request: Request
) -> str:
    """Создает и сохраняет refresh токен в БД, возвращает (raw_token, access_token)"""
    raw_refresh_token, refresh_token_hash = create_refresh_token(user_id)

    if request.client is None or request.client.host is None:
        host = "0.0.0.0"
    else:
        host = request.client.host

    device_info = f"IP: {host}, UA: {request.headers.get('user-agent', 'Unknown')}"
    expires_at = datetime.now(tz=UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    db_token = RefreshTokens(
        user_id=user_id,
        token_hash=refresh_token_hash,
        device_info=device_info,
        expires_at=expires_at,
    )
    session.add(db_token)
    await session.commit()

    return raw_refresh_token


@router.post(
    "/registration",
    summary="Регистрация пользователя",
    description="Регистрация нового пользователя и выдача токенов",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    request: Request,
    response: Response,
    session: AsyncSession = _session_dependency,
):
    conditions = []
    if user.email:
        conditions.append(Users.email == user.email)
    if user.phone:
        conditions.append(Users.phone == user.phone)

    if not conditions:
        raise HTTPException(status_code=400, detail="Нет контактных данных")

    result = await session.exec(select(Users).where(*conditions))
    existing_user = result.first()

    if existing_user:
        msg = "Пользователь с таким Email или Phone уже существует"
        raise HTTPException(status_code=409, detail=msg)

    hashed_password = get_password_hash(user.password)

    new_user = Users(
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        role="user",
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    raw_refresh_token = await create_and_store_refresh_token(
        session, new_user.id, request
    )

    set_refresh_cookie(response, raw_refresh_token)
    return new_user


@router.post(
    "/login",
    summary="Авторизация пользователя",
    description="Авторизация пользователя и выдача токенов",
    response_model=AccessTokenResponse,
)
async def login(
    user_in: UserLogin,
    request: Request,
    response: Response,
    session: AsyncSession = _session_dependency,
):
    statement = select(Users)
    if user_in.email:
        statement = statement.where(Users.email == user_in.email)
    else:
        statement = statement.where(Users.phone == user_in.phone)

    user = session.exec(statement).first()

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    user.last_login = datetime.now(tz=UTC)
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
