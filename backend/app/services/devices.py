from app.models.device import (
    Device,
    DeviceCreateData,
    DeviceUpdateData,
)
from app.repositories.devices import DeviceRepository


class DeviceRegistryError(RuntimeError):
    """Base exception for Device Registry failures."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class DeviceNotFoundError(DeviceRegistryError):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device not found: {device_id}", status_code=404)


class DeviceValidationError(DeviceRegistryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class DeviceService:
    """Application service for physical VPN router devices."""

    def __init__(self, repository: DeviceRepository) -> None:
        self._repository = repository

    async def create_device(self, data: DeviceCreateData) -> Device:
        return await self._repository.create(data)

    async def list_devices(self) -> list[Device]:
        return await self._repository.list()

    async def get_device(self, device_id: str) -> Device:
        device = await self._repository.get(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        return device

    async def update_device(self, device_id: str, data: DeviceUpdateData) -> Device:
        changes = data.model_dump(exclude_unset=True)
        self._validate_update(changes)

        updated = await self._repository.update(device_id, changes)
        if updated is None:
            raise DeviceNotFoundError(device_id)

        return updated

    async def retire_device(self, device_id: str) -> None:
        retired = await self._repository.retire(device_id)
        if retired is None:
            raise DeviceNotFoundError(device_id)

    @staticmethod
    def _validate_update(changes: dict[str, object]) -> None:
        # Optional PATCH fields may be omitted, but core enum fields must not be
        # explicitly cleared to null.
        for field_name in ("status", "activation_status", "platform"):
            if field_name in changes and changes[field_name] is None:
                raise DeviceValidationError(f"{field_name} cannot be null")
