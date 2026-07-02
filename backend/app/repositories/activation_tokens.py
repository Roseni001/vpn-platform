import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.models.activation import (
    DeviceActivationToken,
    DeviceActivationTokenStatus,
)


class ActivationTokenRepository:
    """Temporary process-local activation token repository for CRUD v1.

    This repository is intentionally non-persistent because the project does not
    have a database/persistence layer yet. Data is lost on process restart and
    this must be replaced before production use. Token hashes are stored only
    for MVP backend flow validation.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, DeviceActivationToken] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        *,
        device_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> DeviceActivationToken:
        now = _utc_now()
        token = DeviceActivationToken(
            id=str(uuid4()),
            device_id=device_id,
            token_hash=token_hash,
            status=DeviceActivationTokenStatus.ACTIVE,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )

        async with self._lock:
            self._tokens[token.id] = token

        return token

    async def get_by_hash(self, token_hash: str) -> DeviceActivationToken | None:
        async with self._lock:
            return next(
                (
                    token
                    for token in self._tokens.values()
                    if token.token_hash == token_hash
                ),
                None,
            )

    async def revoke_active_for_device(
        self,
        device_id: str,
    ) -> list[DeviceActivationToken]:
        async with self._lock:
            revoked_tokens: list[DeviceActivationToken] = []

            for token in list(self._tokens.values()):
                if (
                    token.device_id == device_id
                    and token.status == DeviceActivationTokenStatus.ACTIVE
                ):
                    revoked = _replace_token(
                        token,
                        status=DeviceActivationTokenStatus.REVOKED,
                    )
                    self._tokens[token.id] = revoked
                    revoked_tokens.append(revoked)

            return revoked_tokens

    async def mark_used(self, token_id: str) -> DeviceActivationToken | None:
        return await self._update(
            token_id,
            status=DeviceActivationTokenStatus.USED,
            used_at=_utc_now(),
        )

    async def mark_expired(self, token_id: str) -> DeviceActivationToken | None:
        return await self._update(
            token_id,
            status=DeviceActivationTokenStatus.EXPIRED,
        )

    async def _update(
        self,
        token_id: str,
        **changes: object,
    ) -> DeviceActivationToken | None:
        async with self._lock:
            token = self._tokens.get(token_id)
            if token is None:
                return None

            updated = _replace_token(token, **changes)
            self._tokens[token_id] = updated

        return updated


def _replace_token(
    token: DeviceActivationToken,
    **changes: object,
) -> DeviceActivationToken:
    token_data = token.model_dump()
    token_data.update(changes)
    token_data["updated_at"] = _utc_now()
    return DeviceActivationToken(**token_data)


def _utc_now() -> datetime:
    return datetime.now(UTC)
