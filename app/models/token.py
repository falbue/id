from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from app.models.user import Users


class RefreshTokens(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Хеш токена, а не сам токен!
    token_hash: str = Field(unique=True, index=True)

    device_info: str = Field(description="User-Agent, IP и т.д.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_revoked: bool = Field(default=False, description="Мягкое удаление (отзыв)")

    # Связь с пользователем
    user: Users = Relationship(back_populates="refresh_tokens")
