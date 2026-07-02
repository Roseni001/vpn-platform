from app.interfaces.vpn_provider import VPNClient, VPNProvider
from app.models.device import Device, DeviceStatus
from app.models.vpn_assignment import (
    DeviceVPNAssignment,
    ProtocolProfile,
    VPNClientRef,
)
from app.repositories.devices import DeviceRepository
from app.repositories.vpn_assignments import DeviceVPNAssignmentRepository
from app.services.devices import DeviceNotFoundError, DeviceRegistryError

DEFAULT_PROTOCOL_PROFILE = ProtocolProfile(
    id="wireguard_default",
    protocol="wireguard",
    name="WireGuard default",
    provider="wg_easy",
    is_default=True,
    description="Профиль WireGuard по умолчанию для MVP.",
)


class DeviceVPNAssignmentError(DeviceRegistryError):
    """Базовая ошибка назначения VPN-доступа устройству."""


class DeviceVPNAssignmentValidationError(DeviceVPNAssignmentError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class DeviceVPNAssignmentNotFoundError(DeviceVPNAssignmentError):
    def __init__(self, device_id: str) -> None:
        super().__init__(
            f"Active VPN assignment not found for device: {device_id}",
            status_code=404,
        )


class DeviceVPNAssignmentService:
    """Сервис назначения VPN-доступа физическим устройствам."""

    def __init__(
        self,
        *,
        device_repository: DeviceRepository,
        assignment_repository: DeviceVPNAssignmentRepository,
        vpn_provider: VPNProvider,
    ) -> None:
        self._device_repository = device_repository
        self._assignment_repository = assignment_repository
        self._vpn_provider = vpn_provider

    async def create_assignment(self, device_id: str) -> DeviceVPNAssignment:
        device = await self._get_device(device_id)
        owner_user_id = self._validate_device_for_assignment(device)

        if await self._assignment_repository.has_active_for_device(device.id):
            raise DeviceVPNAssignmentValidationError(
                "Device already has an active VPN assignment"
            )

        protocol_profile = self._get_default_protocol_profile()
        vpn_client = await self._vpn_provider.create_client(
            name=self._build_provider_client_name(device)
        )

        return await self._assignment_repository.create(
            device_id=device.id,
            owner_user_id_snapshot=owner_user_id,
            protocol_profile=protocol_profile,
            vpn_client_ref=self._to_vpn_client_ref(vpn_client, protocol_profile),
        )

    async def get_active_assignment(self, device_id: str) -> DeviceVPNAssignment:
        await self._get_device(device_id)

        assignment = await self._assignment_repository.get_active_by_device(device_id)
        if assignment is None:
            raise DeviceVPNAssignmentNotFoundError(device_id)

        return assignment

    async def revoke_assignment(self, device_id: str) -> DeviceVPNAssignment:
        assignment = await self.get_active_assignment(device_id)

        await self._vpn_provider.delete_client(assignment.provider_client_id)

        revoked = await self._assignment_repository.revoke(assignment.id)
        if revoked is None:
            raise DeviceVPNAssignmentNotFoundError(device_id)

        return revoked

    async def list_assignments_by_owner(
        self,
        owner_user_id: str,
    ) -> list[DeviceVPNAssignment]:
        if not owner_user_id.strip():
            raise DeviceVPNAssignmentValidationError("owner_user_id cannot be empty")

        return await self._assignment_repository.list_by_owner(owner_user_id.strip())

    async def _get_device(self, device_id: str) -> Device:
        device = await self._device_repository.get(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        return device

    @staticmethod
    def _validate_device_for_assignment(device: Device) -> str:
        if device.status == DeviceStatus.RETIRED:
            raise DeviceVPNAssignmentValidationError(
                "Retired device cannot receive VPN assignment"
            )

        if device.status == DeviceStatus.DISABLED:
            raise DeviceVPNAssignmentValidationError(
                "Disabled device cannot receive VPN assignment"
            )

        if device.owner_user_id is None or not device.owner_user_id.strip():
            raise DeviceVPNAssignmentValidationError(
                "Device must have owner_user_id before VPN assignment"
            )

        return device.owner_user_id.strip()

    @staticmethod
    def _get_default_protocol_profile() -> ProtocolProfile:
        return DEFAULT_PROTOCOL_PROFILE

    @staticmethod
    def _build_provider_client_name(device: Device) -> str:
        return f"device-{device.id}"

    @staticmethod
    def _to_vpn_client_ref(
        vpn_client: VPNClient,
        protocol_profile: ProtocolProfile,
    ) -> VPNClientRef:
        return VPNClientRef(
            provider=protocol_profile.provider,
            provider_client_id=vpn_client.id,
            provider_client_name=vpn_client.name,
        )
