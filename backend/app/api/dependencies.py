from collections.abc import AsyncIterator

from fastapi import Depends

from app.core.config import Config, get_config
from app.core.container import create_vpn_provider
from app.interfaces.vpn_provider import VPNProvider
from app.services.vpn import VPNService


async def get_vpn_provider(
    config: Config = Depends(get_config),
) -> AsyncIterator[VPNProvider]:
    provider = create_vpn_provider(config)

    try:
        yield provider
    finally:
        close = getattr(provider, "close", None)
        if close is not None:
            await close()


def get_vpn_service(provider: VPNProvider = Depends(get_vpn_provider)) -> VPNService:
    """Build the application service from the provider interface."""
    return VPNService(provider=provider)
