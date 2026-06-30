import logging
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Config
from app.interfaces.vpn_provider import (
    VPNClient,
    VPNClientConfiguration,
    VPNProvider,
    VPNProviderAuthenticationError,
    VPNProviderError,
    VPNProviderNotFoundError,
    VPNProviderUnavailableError,
)

logger = logging.getLogger(__name__)

CLIENTS_PATH = "/api/client"


class WGEasyProvider(VPNProvider):
    """WG-Easy implementation of the VPN provider interface."""

    def __init__(
        self,
        config: Config,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or self._build_client(config)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def list_clients(self) -> list[VPNClient]:
        payload = await self._request_json("GET", CLIENTS_PATH)

        if not isinstance(payload, list):
            raise VPNProviderError("VPN provider clients response has unexpected shape")

        clients: list[VPNClient] = []
        for item in payload:
            if not isinstance(item, Mapping):
                raise VPNProviderError("VPN provider client item has unexpected shape")
            clients.append(self._normalize_client(item))

        return clients

    async def get_client(self, client_id: str) -> VPNClient:
        payload = await self._request_json("GET", self._client_path(client_id))

        if not isinstance(payload, Mapping):
            raise VPNProviderError("VPN provider client response has unexpected shape")

        return self._normalize_client(payload)

    async def create_client(self, name: str) -> VPNClient:
        payload = await self._request_json("POST", CLIENTS_PATH, json={"name": name})

        if not isinstance(payload, Mapping):
            raise VPNProviderError("VPN provider create response has unexpected shape")

        client_id = payload.get("clientId") or payload.get("id")
        if not client_id:
            raise VPNProviderError("VPN provider create response is missing client id")

        return await self.get_client(str(client_id))

    async def delete_client(self, client_id: str) -> None:
        payload = await self._request_json("DELETE", self._client_path(client_id))

        if isinstance(payload, Mapping) and payload.get("success") is False:
            raise VPNProviderError("VPN provider did not delete the client")

    async def get_client_configuration(self, client_id: str) -> VPNClientConfiguration:
        configuration = await self._request_text(
            "GET", self._client_path(client_id, suffix="/configuration")
        )
        return VPNClientConfiguration(client_id=client_id, configuration=configuration)

    @staticmethod
    def _build_client(config: Config) -> httpx.AsyncClient:
        headers = {"Accept": "application/json"}

        if config.wg_easy_api_token:
            token = config.wg_easy_api_token.get_secret_value()
            headers["Authorization"] = f"Bearer {token}"

        return httpx.AsyncClient(
            base_url=str(config.wg_easy_base_url).rstrip("/"),
            timeout=config.wg_easy_timeout_seconds,
            headers=headers,
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        response = await self._send_request(method, path, json=json)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise VPNProviderError("VPN provider returned invalid JSON") from exc

    async def _request_text(self, method: str, path: str) -> str:
        response = await self._send_request(method, path)
        return response.text

    async def _send_request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method=method, url=path, json=json)
        except httpx.TimeoutException as exc:
            raise VPNProviderUnavailableError("VPN provider request timed out") from exc
        except httpx.ConnectError as exc:
            raise VPNProviderUnavailableError("VPN provider is unavailable") from exc
        except httpx.NetworkError as exc:
            raise VPNProviderUnavailableError("VPN provider network error") from exc
        except httpx.RequestError as exc:
            raise VPNProviderUnavailableError("VPN provider request failed") from exc

        if response.status_code == 404:
            raise VPNProviderNotFoundError("VPN client not found")

        if response.status_code in {401, 403}:
            raise VPNProviderAuthenticationError(
                "VPN provider rejected the request",
                status_code=502,
            )

        if response.is_error:
            logger.warning(
                "VPN provider returned HTTP %s for %s %s",
                response.status_code,
                method,
                path,
            )
            raise VPNProviderError("VPN provider request failed")

        return response

    @staticmethod
    def _client_path(client_id: str, *, suffix: str = "") -> str:
        return f"{CLIENTS_PATH}/{quote(client_id, safe='')}{suffix}"

    @staticmethod
    def _normalize_client(client: Mapping[str, Any]) -> VPNClient:
        client_id = client.get("id") or client.get("clientId") or client.get("name")
        if not client_id:
            raise VPNProviderError("VPN provider client item is missing an identifier")

        return VPNClient(
            id=str(client_id),
            name=WGEasyProvider._as_optional_string(client.get("name")),
            enabled=WGEasyProvider._as_bool(client.get("enabled", False)),
            address=WGEasyProvider._as_optional_string(client.get("address")),
            public_key=WGEasyProvider._as_optional_string(
                client.get("publicKey") or client.get("public_key")
            ),
            created_at=WGEasyProvider._as_optional_string(
                client.get("createdAt") or client.get("created_at")
            ),
            updated_at=WGEasyProvider._as_optional_string(
                client.get("updatedAt") or client.get("updated_at")
            ),
        )

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @staticmethod
    def _as_optional_string(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
