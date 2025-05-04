from fastapi import status
from .base import build_response


def bad_request_error(error: str = "Bad request"):
    return build_response(
        status.HTTP_400_BAD_REQUEST,
        "failure",
        error="bad_request",
        message=error,
    )


def conflict_error(error: str = "Credentials already exists"):
    return build_response(
        status.HTTP_409_CONFLICT,
        "failure",
        error="conflict",
        message=error,
    )


def not_found_error(error: str = "Resource not found"):
    return build_response(
        status.HTTP_404_NOT_FOUND,
        "failure",
        error="not_found",
        message=error,
    )


def unauthorized_error(error: str = "Invalid credentials"):
    return build_response(
        status.HTTP_401_UNAUTHORIZED,
        "failure",
        error="unauthorized",
        message=error,
    )


def internal_server_error(error: str = "Internal server error"):
    return build_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "failure",
        error="internal_server_error",
        message=error,
    )


def forbidden_error(error: str = "Access denied"):
    return build_response(
        status.HTTP_403_FORBIDDEN,
        "failure",
        error="forbidden",
        message=error,
    )
