import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.models.device import (
    Device,
    DeviceCreateData,
    DeviceStatus,
)


class DeviceRepository:
    """Temporary process-local device repository for CRUD v1.

    This repository is intentionally non-persistent because the project does not
    have a database/persistence layer yet. Data is lost on process restart and
    this must be replaced before production use.
    """

    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}
        self._lock = asyncio.Lock()

    async def create(self, data: DeviceCreateData) -> Device:
        now = _utc_now()
        device = Device(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )

        async with self._lock:
            self._devices[device.id] = device

        return device

    async def list(self) -> list[Device]:
        async with self._lock:
            return sorted(self._devices.values(), key=lambda device: device.created_at)

    async def get(self, device_id: str) -> Device | None:
        async with self._lock:
            return self._devices.get(device_id)

    async def update(self, device_id: str, changes: dict[str, object]) -> Device | None:
        async with self._lock:
            device = self._devices.get(device_id)
            if device is None:
                return None

            device_data = device.model_dump()
            device_data.update(changes)
            device_data["updated_at"] = _utc_now()

            updated = Device(**device_data)
            self._devices[device_id] = updated

        return updated

    async def retire(self, device_id: str) -> Device | None:
        return await self.update(device_id, {"status": DeviceStatus.RETIRED})


def _utc_now() -> datetime:
    return datetime.now(UTC)
