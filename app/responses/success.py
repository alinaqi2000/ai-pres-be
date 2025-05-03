from .base import build_response


def success_response(message: str, data: dict = None):
    return build_response(200, "success", message, data=data)
