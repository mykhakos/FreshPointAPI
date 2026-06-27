from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Health(BaseModel):
    """Service liveness and readiness summary."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = Field(description='"ok" when ready, "unavailable" otherwise.')
    version: str = Field(description="Running API version.")
    ready: bool = Field(
        description="Whether upstream location data has been loaded at least once."
    )
    known_locations: int = Field(description="Number of known location IDs.")
