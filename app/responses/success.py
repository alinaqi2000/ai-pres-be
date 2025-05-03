from .base import build_response


def success_response(data = None):
    return build_response(200, "success", data=data)

def data_response(data = None):
    return build_response(200, data=data)
