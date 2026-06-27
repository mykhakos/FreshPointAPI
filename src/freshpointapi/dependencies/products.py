from fastapi import Depends, HTTPException, status
from freshpointclient import PageClient
from freshpointparser.models import ProductPage
from freshpointparser.parsers import ParseResult

from ..context import AppContext
from ..params import LocationIdPath
from .common import get_context


async def product_page_client(
    location_id: LocationIdPath,
    context: AppContext = Depends(get_context),
) -> PageClient[ProductPage]:
    if context.known_location_ids and location_id not in context.known_location_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return context.page_client_manager.product_page_client(location_id)


async def product_page_parse_result(
    client: PageClient[ProductPage] = Depends(product_page_client),
) -> ParseResult[ProductPage]:
    result = await client.get()
    return result
