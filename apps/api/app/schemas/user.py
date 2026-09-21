import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleSchema(BaseModel):
    """Role information representation."""

    id: uuid.UUID
    code: str
    label: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Public user identity information."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list, description="Assigned role codes")
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Detailed user profile for GET /auth/me including effective permissions."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list, description="Assigned role codes")
    permissions: list[str] = Field(
        default_factory=list, description="Flattened list of granted permissions"
    )
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
