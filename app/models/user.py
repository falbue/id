from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint


class User(SQLModel, table=True):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "(email IS NOT NULL) OR (phone IS NOT NULL)",
            name="check_email_or_phone_required",
        ),
    )

    id: int = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, unique=True, index=True)
    password_hash: str = Field(min_length=8)
    role: str = Field(default="user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    refresh_tokens: List["RefreshToken"] = Relationship(
        back_populates="user", cascade_delete=True
    )
