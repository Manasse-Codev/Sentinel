import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserContext(BaseModel):
    """Authenticated user authorization context enriched with roles and effective permissions."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list, description="Assigned role codes")
    permissions: set[str] = Field(
        default_factory=set, description="Distinct set of resolved permission codes"
    )
    is_admin: bool = Field(default=False, description="Whether the user holds the admin role")
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
