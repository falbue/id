from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, model_validator
from sqlmodel import Field


class UserRegister(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать либо email, либо phone")
        return self


class UserLogin(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Необходимо указать либо email, либо phone")
        return self


class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    phone: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
