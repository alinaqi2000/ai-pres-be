from fastapi import status
from .base import build_response


def bad_request_error(detail: str):
    return build_response(
        status.HTTP_400_BAD_REQUEST,
        "failure",
        message="Bad request",
        error={"detail": detail},
    )


def conflict_error(detail: str = "Credentials already exists"):
    return build_response(
        status.HTTP_409_CONFLICT,
        "failure",
        message="Conflict error",
        error={"detail": detail},
    )


def not_found_error(detail: str):
    return build_response(
        status.HTTP_404_NOT_FOUND,
        "failure",
        message="Resource not found",
        error={"detail": detail},
    )


def unauthorized_error(detail: str = "Invalid credentials."):
    return build_response(
        status.HTTP_401_UNAUTHORIZED,
        "failure",
        message="Unauthorized access",
        error={"detail": detail},
    )


def internal_server_error(message: str, error: str):
    return {
        "status_code": 500,
        "status": "failure",
        "message": message,
        "data": None,
        "error": {"type": "ServerError", "details": error},
    }
