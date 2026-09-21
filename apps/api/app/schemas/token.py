from pydantic import BaseModel, Field


class Token(BaseModel):
    """Authentication token response schema."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="Opaque refresh token")
    token_type: str = Field(default="bearer", description="Token scheme")
    expires_in: int = Field(description="Access token expiration window in seconds")


class TokenPayload(BaseModel):
    """Decoded JWT claims payload."""

    sub: str = Field(description="Subject (User UUID)")
    email: str = Field(description="User email address")
    roles: list[str] = Field(default_factory=list, description="Assigned role codes")
    exp: int = Field(description="Expiration timestamp (Unix)")
    iat: int = Field(description="Issued at timestamp (Unix)")
    type: str = Field(default="access", description="Token type classifier")


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an expired access token."""

    refresh_token: str = Field(description="Opaque refresh token previously issued")
