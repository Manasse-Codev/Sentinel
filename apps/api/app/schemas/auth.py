from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr = Field(description="User account email address")
    password: str = Field(min_length=1, description="Account plaintext password")


class TokenResponse(BaseModel):
    """Successful authentication response payload."""

    access_token: str = Field(description="Signed JWT access token")
    refresh_token: str = Field(description="Opaque refresh token")
    token_type: str = Field(default="bearer", description="Token scheme")
    expires_in: int = Field(description="Access token lifespan in seconds")
    user: UserResponse = Field(description="Basic authenticated user information")


class RefreshRequest(BaseModel):
    """Payload to refresh an access token."""

    refresh_token: str = Field(min_length=1, description="Previously issued refresh token")


class RefreshResponse(BaseModel):
    """Refreshed token response payload."""

    access_token: str = Field(description="Newly issued JWT access token")
    token_type: str = Field(default="bearer", description="Token scheme")
    expires_in: int = Field(description="Access token lifespan in seconds")


class LogoutRequest(BaseModel):
    """Optional payload for logout specifying a particular refresh token to revoke."""

    refresh_token: str | None = Field(
        default=None, description="Specific refresh token to invalidate"
    )


class MessageResponse(BaseModel):
    """Generic status message response."""

    detail: str
