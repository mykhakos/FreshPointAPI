"""Reusable OpenAPI "additional responses" fragments for the ``responses=`` arg of
route and router declarations. These document responses produced outside the normal
return path — conditional requests and the app's exception handlers — so they show up
in the schema. They do not change behavior.
"""

from dataclasses import dataclass
from typing import Any, Dict, Union

from fastapi import status


@dataclass(frozen=True)
class ResponseInfo:
    """Information about a documented response."""

    status_code: int
    """HTTP status code of the response."""

    description: str
    """Description of the response, shown in the OpenAPI schema."""


NOT_MODIFIED = ResponseInfo(
    status_code=status.HTTP_304_NOT_MODIFIED,
    description="Not Modified",
)
NOT_FOUND = ResponseInfo(
    status_code=status.HTTP_404_NOT_FOUND,
    description="No resource matches the given ID.",
)
BAD_GATEWAY = ResponseInfo(
    status_code=status.HTTP_502_BAD_GATEWAY,
    description=(
        "The upstream FreshPoint source returned an invalid response. Retry later."
    ),
)
GATEWAY_TIMEOUT = ResponseInfo(
    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
    description=(
        "The upstream FreshPoint source did not respond in time. Retry later."
    ),
)
SERVICE_UNAVAILABLE = ResponseInfo(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    description="The service is up but not yet ready (upstream data not loaded).",
)


def response_info_to_dict(
    *responses: ResponseInfo,
) -> Dict[Union[int, str], Dict[str, Any]]:
    """Convert ``ResponseInfo`` objects to a dictionary
    suitable for FastAPI's ``responses=`` argument.

    Args:
        *responses (ResponseInfo): The response information objects to convert.

    Returns:
        Dict[Union[int, str], Dict[str, Any]]: A dictionary mapping status codes
        to response descriptions.
    """
    return {resp.status_code: {"description": resp.description} for resp in responses}
