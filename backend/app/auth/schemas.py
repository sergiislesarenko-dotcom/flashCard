from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

from app.base_schema import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("display_name")
    @classmethod
    def display_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Display name cannot be empty")
        return v.strip()


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class UserResponse(CamelModel):
    id: int
    email: str
    display_name: str
    created_at: datetime


class TokenResponse(CamelModel):
    access_token: str   # → serialised as "accessToken"
    user: UserResponse


class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(CamelModel):
    access_token: str   # → serialised as "accessToken"
