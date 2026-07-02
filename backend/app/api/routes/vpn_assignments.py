from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_device_vpn_assignment_service
from app.services.device_vpn_assignments import DeviceVPNAssignmentService

router = APIRouter(prefix="/vpn-assignments", tags=["vpn-assignments"])


class DeviceVPNAssignmentResponse(BaseModel):
    id: str
    device_id: str
    owner_user_id_snapshot: str
    protocol_profile_id: str
    provider: str
    provider_client_id: str
    provider_client_name: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    assigned_at: datetime | None
    revoked_at: datetime | None


@router.get(
    "/by-owner/{owner_user_id}",
    response_model=list[DeviceVPNAssignmentResponse],
    summary="List VPN assignments by owner",
)
async def list_vpn_assignments_by_owner(
    owner_user_id: str,
    assignment_service: DeviceVPNAssignmentService = Depends(
        get_device_vpn_assignment_service
    ),
) -> list[DeviceVPNAssignmentResponse]:
    assignments = await assignment_service.list_assignments_by_owner(owner_user_id)
    return [
        DeviceVPNAssignmentResponse(**assignment.model_dump())
        for assignment in assignments
    ]
