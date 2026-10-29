from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.token import RefreshToken
from app.models.user import User
from app.routers.dependencies import get_current_user_secure
from app.schemas.token import RefreshTokenInfo

router = APIRouter(prefix="/tokens", tags=["Refresh Tokens"])


@router.get("/", response_model=list[RefreshTokenInfo])
def get_my_tokens(
    current_user: User = Depends(get_current_user_secure),
    session: Session = Depends(get_session),
):
    """Получить список всех активных рефреш-токенов пользователя."""
    # Используем order_by для сортировки по дате создания (новые сверху)
    statement = (
        select(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .order_by(RefreshToken.created_at.desc())
    )
    tokens = session.exec(statement).all()
    return tokens


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
def revoke_all_tokens(
    current_user: User = Depends(get_current_user_secure),
    session: Session = Depends(get_session),
):
    """Выйти со всех устройств (отозвать все активные рефреш-токены)."""
    statement = select(RefreshToken).where(
        RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False
    )
    tokens = session.exec(statement).all()

    for token in tokens:
        token.is_revoked = True

    session.commit()
    return None


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(
    token_id: int,
    current_user: User = Depends(get_current_user_secure),
    session: Session = Depends(get_session),
):
    """Отозвать конкретный рефреш-токен."""
    token = session.get(RefreshToken, token_id)

    # Проверяем существование и принадлежность пользователю
    if not token or token.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Токен не найден или недоступен")

    if token.is_revoked:
        raise HTTPException(status_code=400, detail="Токен уже отозван")

    token.is_revoked = True
    session.commit()
    return None
