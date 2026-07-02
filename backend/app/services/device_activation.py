import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.models.activation import (
    DeviceActivationTokenStatus,
    GeneratedActivationToken,
)
from app.models.device import Device, DeviceActivationStatus, DeviceStatus
from app.repositories.activation_tokens import ActivationTokenRepository
from app.repositories.devices import DeviceRepository
from app.services.devices import DeviceNotFoundError, DeviceRegistryError

ACTIVATION_TOKEN_BYTES = 32
ACTIVATION_TOKEN_TTL = timedelta(hours=24)


class ActivationTokenNotFoundError(DeviceRegistryError):
    def __init__(self) -> None:
        super().__init__("Activation token not found", status_code=404)


class ActivationTokenStateError(DeviceRegistryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class DeviceActivationService:
    """Application service for physical device activation flows."""

    def __init__(
        self,
        *,
        device_repository: DeviceRepository,
        token_repository: ActivationTokenRepository,
    ) -> None:
        self._device_repository = device_repository
        self._token_repository = token_repository

    async def generate_activation_token(
        self,
        device_id: str,
    ) -> GeneratedActivationToken:
        await self._get_device(device_id)

        plain_token = await self._generate_unique_plain_token()
        expires_at = _utc_now() + ACTIVATION_TOKEN_TTL
        await self._token_repository.create(
            device_id=device_id,
            token_hash=_hash_token(plain_token),
            expires_at=expires_at,
        )

        return GeneratedActivationToken(
            device_id=device_id,
            activation_token=plain_token,
            expires_at=expires_at,
        )

    async def revoke_activation(self, device_id: str) -> int:
        await self._get_device(device_id)
        revoked_tokens = await self._token_repository.revoke_active_for_device(device_id)
        return len(revoked_tokens)

    async def activate_manually(self, device_id: str) -> Device:
        device = await self._get_device(device_id)
        return await self._activate_device(device)

    async def activate_by_token(self, plain_token: str) -> Device:
        token = await self._token_repository.get_by_hash(_hash_token(plain_token))
        if token is None:
            raise ActivationTokenNotFoundError()

        if token.status == DeviceActivationTokenStatus.USED:
            raise ActivationTokenStateError("Activation token has already been used")

        if token.status == DeviceActivationTokenStatus.REVOKED:
            raise ActivationTokenStateError("Activation token has been revoked")

        if token.status == DeviceActivationTokenStatus.EXPIRED:
            raise ActivationTokenStateError("Activation token has expired")

        if token.expires_at <= _utc_now():
            await self._token_repository.mark_expired(token.id)
            raise ActivationTokenStateError("Activation token has expired")

        device = await self._get_device(token.device_id)
        # In CRUD v1 the process-local repository is protected per operation.

        # When moved to persistent storage, token validation and marking as used

        # must be atomic to preserve one-time token semantics.
        await self._token_repository.mark_used(token.id)
        return await self._activate_device(device, last_seen_at=_utc_now())

    async def _generate_unique_plain_token(self) -> str:
        while True:
            plain_token = secrets.token_urlsafe(ACTIVATION_TOKEN_BYTES)
            existing = await self._token_repository.get_by_hash(
                _hash_token(plain_token)
            )
            if existing is None:
                return plain_token

    async def _get_device(self, device_id: str) -> Device:
        device = await self._device_repository.get(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        return device

    async def _activate_device(
        self,
        device: Device,
        *,
        last_seen_at: datetime | None = None,
    ) -> Device:
        changes: dict[str, object] = {
            "activation_status": DeviceActivationStatus.ACTIVATED,
        }

        if device.status == DeviceStatus.UNKNOWN:
            changes["status"] = DeviceStatus.REGISTERED

        if last_seen_at is not None:
            changes["last_seen_at"] = last_seen_at

        updated = await self._device_repository.update(device.id, changes)
        if updated is None:
            raise DeviceNotFoundError(device.id)

        return updated


def _hash_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(UTC)
