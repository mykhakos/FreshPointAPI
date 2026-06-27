from enum import Enum
from typing import Any, Dict, List


class Tag(str, Enum):
    """OpenAPI tag names. Single source of truth shared by the routers
    (which assign operations to tags) and ``OPENAPI_TAGS`` (which describes them).
    """

    LOCATIONS = "Locations"
    PRODUCTS = "Products"
    HEALTH = "Health"


OPENAPI_TAGS: List[Dict[str, Any]] = [
    {
        "name": Tag.LOCATIONS,
        "description": "FreshPoint vending locations and their metadata.",
    },
    {
        "name": Tag.PRODUCTS,
        "description": (
            "Products available at a given location, "
            "plus allergen and category lookups."
        ),
    },
    {
        "name": Tag.HEALTH,
        "description": "Service liveness and readiness checks.",
    },
]
