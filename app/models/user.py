from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint


class Users(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "(email IS NOT NULL) OR (phone IS NOT NULL)",
            name="check_email_or_phone_required",
        ),
    )

    id: int = Field(default=None, primary_key=True)
    email: str | None = Field(default=None, unique=True, index=True)
    phone: str | None = Field(default=None, unique=True, index=True)
    password_hash: str = Field(min_length=8)
    role: str = Field(default="user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = Field(default=None)

    refresh_tokens: list = Relationship(back_populates="user", cascade_delete=True)
