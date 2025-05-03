def build_response(
    status_code: int, status: str, message: str, data: dict = None, error: dict = None
):
    return {
        "status_code": status_code,
        "status": status,  # "success" or "failure"
        "message": message,
        "data": data,
        "error": error,
    }
