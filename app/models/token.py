from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from app.models.user import User


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Хеш токена, а не сам токен!
    token_hash: str = Field(unique=True, index=True)

    device_info: str = Field(description="User-Agent, IP и т.д.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_revoked: bool = Field(default=False, description="Мягкое удаление (отзыв)")

    # Связь с пользователем
    user: User = Relationship(back_populates="refresh_tokens")
