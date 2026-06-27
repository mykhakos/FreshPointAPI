import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from freshpointclient import PageClientConfig, PageClientManager
from freshpointclient.exceptions import ClientError, ClientTimeoutError

from .context import AppContext
from .exception_handlers import add_exception_handlers
from .middlewares.etag import ETagMiddleware
from .routers import health, locations, products
from .tags import OPENAPI_TAGS
from .version import API_VERSION

logger = logging.getLogger(__name__)


PAGE_CACHE_MAX_AGE_S = 60.0  # 1 minute
KNOWN_LOCATION_IDS_POLL_INTERVAL_S = 21600.0  # 6 hours


async def poll_known_location_ids(
    context: AppContext, interval_s: float = KNOWN_LOCATION_IDS_POLL_INTERVAL_S
) -> None:
    client = context.page_client_manager.location_page_client()
    while True:
        try:
            result = await client.get()
        except (ClientError, ClientTimeoutError) as exc:
            logger.error("Failed to poll known location IDs: %s", exc)
            await asyncio.sleep(interval_s)
            continue

        context.update_known_location_ids_from_parse_result(result)
        await asyncio.sleep(interval_s)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = PageClientConfig(cache_max_age_s=PAGE_CACHE_MAX_AGE_S)
    async with PageClientManager(config=config) as manager:
        app.state.context = AppContext(page_client_manager=manager)
        poller = asyncio.create_task(poll_known_location_ids(app.state.context))
        try:
            yield
        finally:
            poller.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await poller


async def redirect_to_docs() -> RedirectResponse:
    """Redirect a path to ``/docs``."""
    return RedirectResponse(url="/docs")


def create_app() -> FastAPI:

    app = FastAPI(
        lifespan=lifespan,
        title="FreshPoint API",
        version=API_VERSION,
        summary="Read-only HTTP API over FreshPoint location and product data.",
        license_info={"name": "MIT", "identifier": "MIT"},
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(ETagMiddleware)  # must be added before GZipMiddleware
    app.add_middleware(GZipMiddleware)

    add_exception_handlers(app)

    app.get("/", include_in_schema=False)(redirect_to_docs)
    app.include_router(locations.router)
    app.include_router(products.router)
    app.include_router(health.router)

    return app


app = create_app()
