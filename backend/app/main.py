import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import api_router
from app.core.config import get_config
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    configure_logging(config)

    logger.info(
        "Starting %s version=%s environment=%s",
        config.app_name,
        __version__,
        config.environment,
    )
    yield
    logger.info("Stopping %s", config.app_name)


def create_app() -> FastAPI:
    config = get_config()

    app = FastAPI(
        title=f"{config.app_name} API",
        version=__version__,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
