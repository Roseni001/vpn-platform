import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.models.vpn_assignment import (
    DeviceVPNAssignment,
    DeviceVPNAssignmentStatus,
    ProtocolProfile,
    VPNClientRef,
)


class DeviceVPNAssignmentRepository:
    """Временное process-local хранилище назначений VPN-доступа для v1.

    Хранилище намеренно не является persistent storage: данные теряются после
    рестарта backend и должны быть заменены до production-использования.
    """

    def __init__(self) -> None:
        self._assignments: dict[str, DeviceVPNAssignment] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        *,
        device_id: str,
        owner_user_id_snapshot: str,
        protocol_profile: ProtocolProfile,
        vpn_client_ref: VPNClientRef,
    ) -> DeviceVPNAssignment:
        now = _utc_now()
        assignment = DeviceVPNAssignment(
            id=str(uuid4()),
            device_id=device_id,
            owner_user_id_snapshot=owner_user_id_snapshot,
            protocol_profile_id=protocol_profile.id,
            provider=vpn_client_ref.provider,
            provider_client_id=vpn_client_ref.provider_client_id,
            provider_client_name=vpn_client_ref.provider_client_name,
            status=DeviceVPNAssignmentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            assigned_at=now,
        )

        async with self._lock:
            self._assignments[assignment.id] = assignment

        return assignment

    async def get(self, assignment_id: str) -> DeviceVPNAssignment | None:
        async with self._lock:
            return self._assignments.get(assignment_id)

    async def get_active_by_device(
        self,
        device_id: str,
    ) -> DeviceVPNAssignment | None:
        async with self._lock:
            return next(
                (
                    assignment
                    for assignment in self._assignments.values()
                    if assignment.device_id == device_id
                    and assignment.status == DeviceVPNAssignmentStatus.ACTIVE
                ),
                None,
            )

    async def list_by_owner(self, owner_user_id: str) -> list[DeviceVPNAssignment]:
        async with self._lock:
            return sorted(
                (
                    assignment
                    for assignment in self._assignments.values()
                    if assignment.owner_user_id_snapshot == owner_user_id
                ),
                key=lambda assignment: assignment.created_at,
            )

    async def has_active_for_device(self, device_id: str) -> bool:
        return await self.get_active_by_device(device_id) is not None

    async def revoke(self, assignment_id: str) -> DeviceVPNAssignment | None:
        async with self._lock:
            assignment = self._assignments.get(assignment_id)
            if assignment is None:
                return None

            now = _utc_now()
            assignment_data = assignment.model_dump()
            assignment_data.update(
                {
                    "status": DeviceVPNAssignmentStatus.REVOKED,
                    "revoked_at": now,
                    "updated_at": now,
                }
            )

            revoked = DeviceVPNAssignment(**assignment_data)
            self._assignments[assignment_id] = revoked

        return revoked


def _utc_now() -> datetime:
    return datetime.now(UTC)
