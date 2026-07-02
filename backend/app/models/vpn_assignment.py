from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DeviceVPNAssignmentStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    FAILED = "failed"


class ProtocolProfile(BaseModel):
    id: str
    protocol: str
    name: str
    provider: str
    is_default: bool = False
    description: str | None = None

    model_config = ConfigDict(extra="forbid")


class VPNClientRef(BaseModel):
    provider: str
    provider_client_id: str
    provider_client_name: str | None = None

    model_config = ConfigDict(extra="forbid")


class DeviceVPNAssignment(BaseModel):
    id: str
    device_id: str
    owner_user_id_snapshot: str
    protocol_profile_id: str
    provider: str
    provider_client_id: str
    provider_client_name: str | None = None
    status: DeviceVPNAssignmentStatus
    created_at: datetime
    updated_at: datetime
    assigned_at: datetime | None = None
    revoked_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")
