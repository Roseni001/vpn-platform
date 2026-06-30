from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Config, get_config

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
)
async def health(config: Config = Depends(get_config)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=config.app_name,
        environment=config.environment,
    )
