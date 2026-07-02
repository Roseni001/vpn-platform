from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DeviceStatus(StrEnum):
    UNKNOWN = "unknown"
    REGISTERED = "registered"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DISABLED = "disabled"
    RETIRED = "retired"


class DeviceActivationStatus(StrEnum):
    NOT_ACTIVATED = "not_activated"
    ACTIVATION_PENDING = "activation_pending"
    ACTIVATED = "activated"
    ACTIVATION_FAILED = "activation_failed"
    REVOKED = "revoked"


class DevicePlatform(StrEnum):
    OPENWRT = "openwrt"
    STOCK_FIRMWARE = "stock_firmware"
    UNKNOWN = "unknown"
    FUTURE = "future"


class Device(BaseModel):
    id: str
    name: str | None = None
    status: DeviceStatus
    activation_status: DeviceActivationStatus
    owner_user_id: str | None = None
    router_model: str | None = None
    router_revision: str | None = None
    serial_number: str | None = None
    hardware_id: str | None = None
    mac_address: str | None = None
    firmware_version: str | None = None
    openwrt_version: str | None = None
    architecture: str | None = None
    platform: DevicePlatform
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="forbid")


class DeviceCreateData(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    status: DeviceStatus = DeviceStatus.REGISTERED
    activation_status: DeviceActivationStatus = DeviceActivationStatus.NOT_ACTIVATED
    owner_user_id: str | None = Field(default=None, min_length=1, max_length=128)
    router_model: str | None = Field(default=None, min_length=1, max_length=128)
    router_revision: str | None = Field(default=None, min_length=1, max_length=64)
    serial_number: str | None = Field(default=None, min_length=1, max_length=128)
    hardware_id: str | None = Field(default=None, min_length=1, max_length=128)
    mac_address: str | None = Field(default=None, min_length=1, max_length=32)
    firmware_version: str | None = Field(default=None, min_length=1, max_length=128)
    openwrt_version: str | None = Field(default=None, min_length=1, max_length=64)
    architecture: str | None = Field(default=None, min_length=1, max_length=64)
    platform: DevicePlatform = DevicePlatform.UNKNOWN
    last_seen_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class DeviceUpdateData(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    status: DeviceStatus | None = None
    activation_status: DeviceActivationStatus | None = None
    owner_user_id: str | None = Field(default=None, min_length=1, max_length=128)
    router_model: str | None = Field(default=None, min_length=1, max_length=128)
    router_revision: str | None = Field(default=None, min_length=1, max_length=64)
    serial_number: str | None = Field(default=None, min_length=1, max_length=128)
    hardware_id: str | None = Field(default=None, min_length=1, max_length=128)
    mac_address: str | None = Field(default=None, min_length=1, max_length=32)
    firmware_version: str | None = Field(default=None, min_length=1, max_length=128)
    openwrt_version: str | None = Field(default=None, min_length=1, max_length=64)
    architecture: str | None = Field(default=None, min_length=1, max_length=64)
    platform: DevicePlatform | None = None
    last_seen_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")
