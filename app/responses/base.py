from fastapi import Response
from fastapi.responses import JSONResponse
from typing import Optional


def build_response(
    status_code: int,
    status: str = None,
    message: str = None,
    data=None,
    error: Optional[str] = None,
) -> Response:
    if status_code == 204:
        return Response(status_code=204)

    response = {}

    if status is not None:
        response["status"] = status

    if message is not None:
        response["message"] = message

    if data is not None:
        response["data"] = data

    if error is not None:
        response["error"] = error

    return JSONResponse(content=response, status_code=status_code)
