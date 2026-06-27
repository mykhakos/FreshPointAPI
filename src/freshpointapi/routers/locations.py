from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from freshpointclient import PageClient
from freshpointparser.filters import LocationFilter, LocationNearbyFilter
from freshpointparser.models import Location, LocationPage
from freshpointparser.parsers import ParseResult
from typing_extensions import Annotated

from ..additional_responses import (
    BAD_GATEWAY,
    GATEWAY_TIMEOUT,
    NOT_FOUND,
    NOT_MODIFIED,
    response_info_to_dict,
)
from ..dependencies.locations import location_page_client, location_page_parse_result
from ..params import LocationIdPath
from ..schemas.locations import LocationNearby
from ..tags import Tag

router = APIRouter(
    prefix="/locations",
    tags=[Tag.LOCATIONS],
    responses=response_info_to_dict(BAD_GATEWAY, GATEWAY_TIMEOUT),
)


@router.get(
    "",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def list_locations(
    filter_: Annotated[LocationFilter, Query()] = LocationFilter(),
    result: ParseResult[LocationPage] = Depends(location_page_parse_result),
) -> List[Location]:
    return list(result.page.find_items(filter_))


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_locations(
    client: PageClient[LocationPage] = Depends(location_page_client),
) -> None:
    await client.get(force_refresh=True)


@router.get(
    "/nearby",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def locations_nearby(
    filter_: Annotated[LocationNearbyFilter, Query()],
    result: ParseResult[LocationPage] = Depends(location_page_parse_result),
) -> List[LocationNearby]:
    locations = []
    for loc in result.page.find_items(filter_):
        loc_data = loc.model_dump(exclude_unset=True)
        loc_data["distance"] = loc.distance_from(filter_.latitude, filter_.longitude)
        locations.append(LocationNearby.model_validate(loc_data))
    return sorted(locations, key=lambda loc: loc.distance)


@router.get(
    "/{locationId}",
    responses=response_info_to_dict(NOT_MODIFIED, NOT_FOUND),
    response_model_exclude_none=True,
)
async def get_location(
    location_id: LocationIdPath,
    result: ParseResult[LocationPage] = Depends(location_page_parse_result),
) -> Location:
    locations = {loc.id_: loc for loc in result.page.items if loc.id_ is not None}
    try:
        return locations[location_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        ) from None
