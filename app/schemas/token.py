from datetime import datetime
from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenInfo(BaseModel):
    id: int
    device_info: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
