from fastapi import APIRouter

from app.api.routes import clients, devices, health, vpn_assignments

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(clients.router)
api_router.include_router(devices.router)
api_router.include_router(vpn_assignments.router)
