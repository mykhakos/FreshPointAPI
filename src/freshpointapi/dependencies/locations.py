from fastapi import Depends
from freshpointclient import PageClient
from freshpointparser.models import LocationPage
from freshpointparser.parsers import ParseResult

from ..context import AppContext
from .common import get_context


async def location_page_client(
    context: AppContext = Depends(get_context),
) -> PageClient[LocationPage]:
    return context.page_client_manager.location_page_client()


async def location_page_parse_result(
    context: AppContext = Depends(get_context),
    client: PageClient[LocationPage] = Depends(location_page_client),
) -> ParseResult[LocationPage]:
    result = await client.get()
    context.update_known_location_ids_from_parse_result(result)
    return result
