from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DeviceActivationTokenStatus(StrEnum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DeviceActivationToken(BaseModel):
    id: str
    device_id: str
    token_hash: str
    status: DeviceActivationTokenStatus
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class GeneratedActivationToken(BaseModel):
    device_id: str
    activation_token: str
    expires_at: datetime

    model_config = ConfigDict(extra="forbid")
