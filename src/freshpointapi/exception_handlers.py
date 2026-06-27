from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from freshpointclient.exceptions import (
    ClientError,
    ClientTimeoutError,
    PageNotFoundError,
)


def handle_client_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ClientError):
        raise TypeError(f"Expected ClientError, got {type(exc)}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Upstream error"},
    )


def handle_client_timeout_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ClientTimeoutError):
        raise TypeError(f"Expected ClientTimeoutError, got {type(exc)}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "Upstream timeout"},
    )


def handle_page_not_found_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, PageNotFoundError):
        raise TypeError(f"Expected PageNotFoundError, got {type(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Location not found"},
    )


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ClientError, handle_client_error)
    app.add_exception_handler(ClientTimeoutError, handle_client_timeout_error)
    app.add_exception_handler(PageNotFoundError, handle_page_not_found_error)
