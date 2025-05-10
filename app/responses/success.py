from .base import build_response
from pydantic import BaseModel
from typing import Any


def success_response(message: str = None, data=None):
    return build_response(200, "success", message=message, data=data)


def data_response(data=None):
    return build_response(200, status='success', data=data)


def empty_response():
    return build_response(204)
