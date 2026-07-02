from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_device_service
from app.models.device import (
    Device,
    DeviceActivationStatus,
    DeviceCreateData,
    DevicePlatform,
    DeviceStatus,
    DeviceUpdateData,
)
from app.services.devices import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceCreateRequest(BaseModel):
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


class DeviceUpdateRequest(BaseModel):
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


class DeviceResponse(BaseModel):
    id: str
    name: str | None
    status: DeviceStatus
    activation_status: DeviceActivationStatus
    owner_user_id: str | None
    router_model: str | None
    router_revision: str | None
    serial_number: str | None
    hardware_id: str | None
    mac_address: str | None
    firmware_version: str | None
    openwrt_version: str | None
    architecture: str | None
    platform: DevicePlatform
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


def to_device_response(device: Device) -> DeviceResponse:
    return DeviceResponse(**device.model_dump())


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create physical device",
)
async def create_device(
    payload: DeviceCreateRequest,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    device = await device_service.create_device(
        DeviceCreateData(**payload.model_dump())
    )
    return to_device_response(device)


@router.get(
    "",
    response_model=list[DeviceResponse],
    summary="List physical devices",
)
async def list_devices(
    device_service: DeviceService = Depends(get_device_service),
) -> list[DeviceResponse]:
    devices = await device_service.list_devices()
    return [to_device_response(device) for device in devices]


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get physical device",
)
async def get_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    device = await device_service.get_device(device_id)
    return to_device_response(device)


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update physical device",
)
async def update_device(
    device_id: str,
    payload: DeviceUpdateRequest,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    device = await device_service.update_device(
        device_id,
        DeviceUpdateData(**payload.model_dump(exclude_unset=True)),
    )
    return to_device_response(device)


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retire physical device",
)
async def delete_device(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
) -> Response:
    await device_service.retire_device(device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
