from fastapi import Path
from typing_extensions import Annotated

LocationIdPath = Annotated[
    str, Path(alias="locationId", description="The ID of the location.")
]
ProductIdPath = Annotated[
    str, Path(alias="productId", description="The ID of the product.")
]
