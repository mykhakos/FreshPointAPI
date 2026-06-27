from base64 import b64encode
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, Final, Optional

from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class Header:
    """HTTP header names used by ETagMiddleware (Enum-like namespace)."""

    ETAG: Final = "etag"
    IF_NONE_MATCH: Final = "if-none-match"
    CACHE_CONTROL: Final = "cache-control"
    VARY: Final = "vary"
    CONTENT_LENGTH: Final = "content-length"
    CONTENT_LOCATION: Final = "content-location"
    EXPIRES: Final = "expires"


@dataclass(frozen=True)
class ETag:
    """A weak HTTP entity-tag."""

    value: str
    """Opaque token, e.g. ``abc123`` (no ``W/`` prefix, no quotes)."""

    @classmethod
    def from_response_body(cls, body: bytes) -> "ETag":
        """Derive an ETag from the response body by hashing it.

        Hashing algorithm is SHA-256 to comply with FIPS.
        The digest is base64-encoded with padding stripped.

        Args:
            body (bytes): The response body.

        Returns:
            ETag: The derived ETag.
        """
        return cls(value=b64encode(sha256(body).digest()).rstrip(b"=").decode("ascii"))

    @property
    def header_value(self) -> str:
        """``value`` rendered as a weak ETag header value, e.g. ``W/"abc123"``."""
        return f'W/"{self.value}"'

    def is_matched_by(self, if_none_match: Optional[str]) -> bool:
        """Check whether this ETag matches the client's ``If-None-Match`` header.

        Implements the weak comparison of RFC 9110 §8.8.3.2
        (the ``W/`` prefix is ignored) and supports the ``*`` wildcard
        and comma-separated lists of RFC 9110 §13.1.2.

        Args:
            if_none_match (Optional[str]): ``If-None-Match`` header sent by the client.

        Returns:
            bool: Whether the header matches this ETag.
        """
        if not if_none_match:
            return False
        header = if_none_match.strip()
        if header == "*":
            return True
        return any(self._normalize_tag(tag) == self.value for tag in header.split(","))

    @staticmethod
    def _normalize_tag(raw_tag: str) -> str:
        """Reduce a raw ``If-None-Match`` entry to its bare opaque token."""
        tag = raw_tag.strip()
        if tag.startswith("W/"):
            tag = tag[2:]
        return tag.strip('"')


class ETagMiddleware(BaseHTTPMiddleware):
    """Tags GET/HEAD ``200`` responses with a weak ETag derived from the response body
    and serves ``304 Not Modified`` if the client's ``If-None-Match`` matches the tag.
    """

    NOT_MODIFIED_HEADERS = frozenset(
        (
            Header.ETAG,
            Header.CACHE_CONTROL,
            Header.VARY,
            Header.CONTENT_LOCATION,
            Header.EXPIRES,
        )
    )
    """Response headers that are preserved when building the 304 Not Modified response.

    (See RFC 9110 §15.4.5.)
    """

    _BODY_ITERATOR_ATTR = "body_iterator"
    """The attribute name that the response body stream is expected to be on."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Tag eligible responses with an ETag. Short-circuit to 304 on a match.

        Implements required ``BaseHTTPMiddleware`` interface.

        Args:
            request (Request): The incoming HTTP request.
            call_next (RequestResponseEndpoint): The next middleware or endpoint in the chain.

        Returns:
            Response: The HTTP response to be sent back to the client.
        """
        response = await call_next(request)
        if not self._is_etaggable(request, response):
            return response

        body = await self._read_body(response)
        etag = ETag.from_response_body(body)
        if etag.is_matched_by(request.headers.get(Header.IF_NONE_MATCH)):
            return self._not_modified(response, etag)
        else:
            return self._tagged(response, body, etag)

    @classmethod
    def _is_etaggable(cls, request: Request, response: Response) -> bool:
        """Check whether the response is eligible for ETag tagging.

        Args:
            request (Request): The incoming HTTP request.
            response (Response): The HTTP response to be checked.

        Returns:
            bool: True if the response is eligible for ETag tagging, False otherwise.
        """
        return (
            request.method in ("GET", "HEAD")
            and response.status_code == status.HTTP_200_OK
            and hasattr(response, cls._BODY_ITERATOR_ATTR)  # has readable body
            and Header.CONTENT_LENGTH in response.headers  # not StreamingResponse
            and Header.ETAG not in response.headers  # ETag not present
        )

    @classmethod
    async def _read_body(cls, response: Response) -> bytes:
        """Buffer the streamed body chunks emitted by ``BaseHTTPMiddleware.call_next``.

        Args:
            response (Response): The HTTP response whose body is to be buffered.

        Raises:
            TypeError: If a body chunk is neither bytes nor str.

        Returns:
            bytes: The buffered body.
        """
        chunks = []
        async for chunk in getattr(response, cls._BODY_ITERATOR_ATTR):
            if isinstance(chunk, bytes):
                chunks.append(chunk)
            elif isinstance(chunk, str):
                chunks.append(chunk.encode())
            else:
                raise TypeError(
                    f"Unexpected body chunk type '{type(chunk)!r}' "
                    f"(expected bytes or str)."
                )
        return b"".join(chunks)

    @staticmethod
    def _update_headers_for_etag(headers: Dict, etag: ETag) -> None:
        """Update the response headers to include the ETag and cache control.

        Args:
            headers (Dict): The response headers to be updated.
            etag (ETag): The ETag to be included in the headers.
        """
        headers[Header.ETAG] = etag.header_value
        headers.setdefault(Header.CACHE_CONTROL, "public, no-cache")

    @classmethod
    def _not_modified(cls, response: Response, etag: ETag) -> Response:
        """Build a bodyless 304 Not Modified response with relevant headers.

        Args:
            response (Response): The original HTTP response.
            etag (ETag): The ETag to be included in the response.

        Returns:
            Response: A 304 Not Modified response with the appropriate headers.
        """
        headers = {
            key: value
            for key, value in response.headers.items()
            if key in cls.NOT_MODIFIED_HEADERS
        }
        cls._update_headers_for_etag(headers, etag)
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    @classmethod
    def _tagged(cls, response: Response, body: bytes, etag: ETag) -> Response:
        """Build a 200 OK response with the buffered body.

        Rebuilding lets ``Response`` recompute Content-Length.

        Args:
            response (Response): The original HTTP response.
            body (bytes): The response body to be attached.
            etag (ETag): The ETag to be included in the response.

        Returns:
            Response: A 200 OK response with the buffered body and the ETag attached.
        """
        headers = dict(response.headers)
        cls._update_headers_for_etag(headers, etag)
        # BackgroundTask is not carried over (unnecessary, already ran inside call_next)
        return Response(content=body, status_code=status.HTTP_200_OK, headers=headers)
