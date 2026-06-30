from app.interfaces.vpn_provider import (
    VPNClient,
    VPNClientConfiguration,
    VPNProvider,
)


class VPNService:
    """Application service for VPN operations."""

    def __init__(self, provider: VPNProvider) -> None:
        self._provider = provider

    async def list_clients(self) -> list[VPNClient]:
        return await self._provider.list_clients()

    async def get_client(self, client_id: str) -> VPNClient:
        return await self._provider.get_client(client_id)

    async def create_client(self, name: str) -> VPNClient:
        return await self._provider.create_client(name)

    async def delete_client(self, client_id: str) -> None:
        await self._provider.delete_client(client_id)

    async def get_client_configuration(self, client_id: str) -> VPNClientConfiguration:
        return await self._provider.get_client_configuration(client_id)
