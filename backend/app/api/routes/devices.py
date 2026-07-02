from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_device_activation_service, get_device_service
from app.models.device import (
    Device,
    DeviceActivationStatus,
    DeviceCreateData,
    DevicePlatform,
    DeviceStatus,
    DeviceUpdateData,
)
from app.services.device_activation import DeviceActivationService
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


class AssignOwnerRequest(BaseModel):
    owner_user_id: str = Field(min_length=1, max_length=128)

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


class ActivationTokenResponse(BaseModel):
    device_id: str
    activation_token: str
    expires_at: datetime


class ActivationRequest(BaseModel):
    activation_token: str = Field(min_length=1, max_length=256)

    model_config = ConfigDict(extra="forbid")


class RevokeActivationResponse(BaseModel):
    device_id: str
    activation_status: DeviceActivationStatus
    revoked_tokens: int


def to_device_response(device: Device) -> DeviceResponse:
    return DeviceResponse(**device.model_dump())


@router.post(
    "/activate",
    response_model=DeviceResponse,
    summary="Activate physical device by token",
)
async def activate_device_by_token(
    payload: ActivationRequest,
    activation_service: DeviceActivationService = Depends(
        get_device_activation_service
    ),
) -> DeviceResponse:
    device = await activation_service.activate_by_token(payload.activation_token)
    return to_device_response(device)


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
    "/by-owner/{owner_user_id}",
    response_model=list[DeviceResponse],
    summary="List physical devices by owner",
)
async def list_devices_by_owner(
    owner_user_id: str,
    device_service: DeviceService = Depends(get_device_service),
) -> list[DeviceResponse]:
    devices = await device_service.list_devices_by_owner(owner_user_id)
    return [to_device_response(device) for device in devices]


@router.post(
    "/{device_id}/activation-token",
    response_model=ActivationTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate device activation token",
)
async def generate_activation_token(
    device_id: str,
    activation_service: DeviceActivationService = Depends(
        get_device_activation_service
    ),
) -> ActivationTokenResponse:
    generated = await activation_service.generate_activation_token(device_id)
    return ActivationTokenResponse(**generated.model_dump())


@router.post(
    "/{device_id}/revoke-activation",
    response_model=RevokeActivationResponse,
    summary="Revoke active device activation tokens",
)
async def revoke_activation(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
    activation_service: DeviceActivationService = Depends(
        get_device_activation_service
    ),
) -> RevokeActivationResponse:
    revoked_tokens = await activation_service.revoke_activation(device_id)
    device = await device_service.get_device(device_id)
    return RevokeActivationResponse(
        device_id=device.id,
        activation_status=device.activation_status,
        revoked_tokens=revoked_tokens,
    )


@router.post(
    "/{device_id}/activate-manually",
    response_model=DeviceResponse,
    summary="Manually activate physical device",
)
async def activate_device_manually(
    device_id: str,
    activation_service: DeviceActivationService = Depends(
        get_device_activation_service
    ),
) -> DeviceResponse:
    device = await activation_service.activate_manually(device_id)
    return to_device_response(device)


@router.post(
    "/{device_id}/assign-owner",
    response_model=DeviceResponse,
    summary="Assign physical device owner",
)
async def assign_device_owner(
    device_id: str,
    payload: AssignOwnerRequest,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    device = await device_service.assign_owner(device_id, payload.owner_user_id)
    return to_device_response(device)


@router.post(
    "/{device_id}/unassign-owner",
    response_model=DeviceResponse,
    summary="Unassign physical device owner",
)
async def unassign_device_owner(
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    device = await device_service.unassign_owner(device_id)
    return to_device_response(device)


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
