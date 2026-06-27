from freshpointparser.models import Location
from pydantic import Field


class LocationNearby(Location):
    """A matched location plus its distance from the query origin."""

    distance: int = Field(description="Distance from the query origin in meters.")
