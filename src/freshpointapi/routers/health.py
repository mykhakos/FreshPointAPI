from fastapi import APIRouter, Depends, Response, status

from ..additional_responses import SERVICE_UNAVAILABLE, response_info_to_dict
from ..context import AppContext
from ..dependencies.common import get_context
from ..schemas.health import Health
from ..tags import Tag
from ..version import API_VERSION

router = APIRouter(prefix="/health", tags=[Tag.HEALTH])


@router.get("", responses=response_info_to_dict(SERVICE_UNAVAILABLE))
async def health(
    response: Response,
    context: AppContext = Depends(get_context),
) -> Health:
    ready = bool(context.known_location_ids)
    if ready:
        status_message = "ok"
        response.status_code = status.HTTP_200_OK
    else:
        status_message = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(
        status=status_message,
        version=API_VERSION,
        ready=ready,
        known_locations=len(context.known_location_ids),
    )
