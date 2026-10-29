from datetime import UTC, datetime

from pydantic import model_validator
from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel


class BaseModel(SQLModel):
    email: str = Field(default=None, unique=True, index=True)
    phone: str = Field(default=None, unique=True, index=True)
    role: str = Field(default="user")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: datetime = Field(default_factory=lambda: datetime.now(UTC))

    refresh_tokens = Relationship(back_populates="user", cascade_delete=True)

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать либо email, либо phone")
        return self


class Users(BaseModel, table=True):
    __table_args__ = (
        CheckConstraint(
            sqltext="(email IS NOT NULL) OR (phone IS NOT NULL)",
            name="check_email_or_phone_required",
        ),
    )

    id: int = Field(default=None, primary_key=True)
    password_hash: str = Field(description="Хэш пароля")


class UserCreate(SQLModel):
    email: str = Field(
        default="",
        description="Рекомендую указывать почту, так как проверки на телефон пока никакой нет",
    )
    phone: str = Field(default="")
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать либо email, либо phone")
        return self


class UserLogin(SQLModel):
    email: str = ""
    phone: str = ""
    password: str

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать либо email, либо phone")
        return self


class UserResponse(BaseModel):
    id: int
