from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class VPNClient(BaseModel):
    id: str
    name: str | None = None
    enabled: bool
    address: str | None = None
    public_key: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(extra="ignore")


class VPNClientConfiguration(BaseModel):
    client_id: str
    configuration: str
    filename: str | None = None

    model_config = ConfigDict(extra="ignore")


class VPNProviderError(RuntimeError):
    """Base exception for VPN provider integration failures."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class VPNProviderAuthenticationError(VPNProviderError):
    """Raised when an upstream VPN provider rejects the request."""


class VPNProviderUnavailableError(VPNProviderError):
    """Raised when an upstream VPN provider cannot be reached."""


class VPNProviderNotFoundError(VPNProviderError):
    """Raised when an upstream VPN provider resource does not exist."""

    def __init__(self, message: str = "VPN provider resource not found") -> None:
        super().__init__(message, status_code=404)


class VPNProvider(ABC):
    """Interface for VPN provider integrations."""

    @abstractmethod
    async def list_clients(self) -> list[VPNClient]:
        """Return VPN clients known to the provider."""
        raise NotImplementedError

    @abstractmethod
    async def get_client(self, client_id: str) -> VPNClient:
        """Return a single VPN client by provider-specific identifier."""
        raise NotImplementedError

    @abstractmethod
    async def create_client(self, name: str) -> VPNClient:
        """Create and return a VPN client."""
        raise NotImplementedError

    @abstractmethod
    async def delete_client(self, client_id: str) -> None:
        """Delete a VPN client by provider-specific identifier."""
        raise NotImplementedError

    @abstractmethod
    async def get_client_configuration(self, client_id: str) -> VPNClientConfiguration:
        """Return a client VPN configuration."""
        raise NotImplementedError
