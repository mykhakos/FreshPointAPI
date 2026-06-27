from fastapi import Request

from ..context import AppContext


async def get_context(request: Request) -> AppContext:
    return request.app.state.context
