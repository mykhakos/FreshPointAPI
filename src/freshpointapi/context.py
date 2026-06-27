import logging
from typing import Iterable, Set

from freshpointclient import PageClientManager
from freshpointparser.models import LocationPage
from freshpointparser.parsers import ParseResult
from typing_extensions import FrozenSet

logger = logging.getLogger(__name__)


class AppContext:
    def __init__(self, page_client_manager: PageClientManager) -> None:
        self._page_client_manager = page_client_manager
        self._known_location_ids: Set[str] = set()

    @property
    def page_client_manager(self) -> PageClientManager:
        """Get the page client manager."""
        return self._page_client_manager

    @property
    def known_location_ids(self) -> FrozenSet[str]:
        """Get the known location IDs."""
        return frozenset(self._known_location_ids)

    def update_known_location_ids(self, location_ids: Iterable[str]) -> None:
        """Update the known location IDs in the app context."""
        location_ids_as_set = set(location_ids)
        if self._known_location_ids != location_ids_as_set:
            logger.info(
                "Updating known location IDs (was %s, now %s)",
                len(self._known_location_ids),
                len(location_ids_as_set),
            )
            self._known_location_ids.update(location_ids_as_set)
        else:
            logger.debug(
                "Known location IDs are up-to-date (now %s)",
                len(location_ids_as_set),
            )

    def update_known_location_ids_from_parse_result(
        self, result: ParseResult[LocationPage]
    ) -> None:
        """Update the known location IDs in the app context from a parse result."""
        known_location_ids = tuple(
            location.id_ for location in result.page.items if location.id_ is not None
        )
        if known_location_ids:
            self.update_known_location_ids(known_location_ids)
        else:
            logger.warning(
                "No location IDs found on location page %s. ", result.page.url
            )
