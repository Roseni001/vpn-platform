import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.interfaces.vpn_provider import VPNProviderError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers for the HTTP API."""

    @app.exception_handler(VPNProviderError)
    async def handle_provider_error(
        request: Request,
        exc: VPNProviderError,
    ) -> JSONResponse:
        logger.warning("Provider error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )

    @app.exception_handler(httpx.HTTPError)
    async def handle_http_error(request: Request, exc: httpx.HTTPError) -> JSONResponse:
        logger.warning("HTTP client error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=502,
            content={"detail": "Upstream service unavailable"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
