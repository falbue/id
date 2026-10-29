from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.entities.user import Users


class BaseModel(SQLModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokens(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True)
    device_info: str = Field(description="User-Agent, IP и т.д.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    is_revoked: bool = Field(default=False, description="Мягкое удаление (отзыв)")
    user: Users = Relationship(back_populates="refresh_tokens")


class TokenPair(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    pass


class RefreshTokenInfo(SQLModel):
    id: int
    device_info: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
