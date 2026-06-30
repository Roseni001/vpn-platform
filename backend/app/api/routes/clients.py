from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_vpn_service
from app.interfaces.vpn_provider import VPNClient
from app.services.vpn import VPNService

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientResponse(BaseModel):
    id: str
    name: str | None
    enabled: bool
    address: str | None
    public_key: str | None
    created_at: str | None
    updated_at: str | None


class ClientCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ClientConfigurationResponse(BaseModel):
    client_id: str
    configuration: str


def to_client_response(client: VPNClient) -> ClientResponse:
    return ClientResponse(**client.model_dump())


@router.get(
    "",
    response_model=list[ClientResponse],
    summary="List VPN clients",
)
async def list_clients(
    vpn_service: VPNService = Depends(get_vpn_service),
) -> list[ClientResponse]:
    return [to_client_response(client) for client in await vpn_service.list_clients()]


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get VPN client",
)
async def get_client(
    client_id: str,
    vpn_service: VPNService = Depends(get_vpn_service),
) -> ClientResponse:
    client = await vpn_service.get_client(client_id)
    return to_client_response(client)


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create VPN client",
)
async def create_client(
    payload: ClientCreateRequest,
    vpn_service: VPNService = Depends(get_vpn_service),
) -> ClientResponse:
    client = await vpn_service.create_client(name=payload.name)
    return to_client_response(client)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete VPN client",
)
async def delete_client(
    client_id: str,
    vpn_service: VPNService = Depends(get_vpn_service),
) -> Response:
    await vpn_service.delete_client(client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{client_id}/configuration",
    response_model=ClientConfigurationResponse,
    summary="Get VPN client configuration",
)
async def get_client_configuration(
    client_id: str,
    vpn_service: VPNService = Depends(get_vpn_service),
) -> ClientConfigurationResponse:
    configuration = await vpn_service.get_client_configuration(client_id)
    return ClientConfigurationResponse(
        client_id=configuration.client_id,
        configuration=configuration.configuration,
    )
