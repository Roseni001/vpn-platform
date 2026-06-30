from app.core.config import Config
from app.interfaces.vpn_provider import VPNProvider
from app.providers.wg_easy import WGEasyProvider


def create_vpn_provider(config: Config) -> VPNProvider:
    """Compose the configured VPN provider implementation.

    This is the only place where the application chooses WG-Easy.
    """
    return WGEasyProvider(config=config)
