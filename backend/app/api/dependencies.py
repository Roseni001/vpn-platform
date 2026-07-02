from collections.abc import AsyncIterator

from fastapi import Depends

from app.core.config import Config, get_config
from app.core.container import create_vpn_provider
from app.interfaces.vpn_provider import VPNProvider
from app.repositories.activation_tokens import ActivationTokenRepository
from app.repositories.devices import DeviceRepository
from app.services.device_activation import DeviceActivationService
from app.services.devices import DeviceService
from app.services.vpn import VPNService

_device_repository = DeviceRepository()
_activation_token_repository = ActivationTokenRepository()


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


def get_device_service() -> DeviceService:
    """Build the Device Registry service."""
    return DeviceService(repository=_device_repository)


def get_device_activation_service() -> DeviceActivationService:
    """Build the Device Activation service."""
    return DeviceActivationService(
        device_repository=_device_repository,
        token_repository=_activation_token_repository,
    )
