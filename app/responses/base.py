from fastapi import Response
from fastapi.responses import JSONResponse
from typing import Optional, Any, Union
from pydantic import BaseModel
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Filter out Depends objects
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Depends':
            return None
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        # Handle other custom types or return string representation
        return str(obj)

def build_response(
    status_code: int,
    status: str = None,
    message: str = None,
    data: Any = None,
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
        # If data is a Pydantic model, convert it to a dictionary
        if isinstance(data, BaseModel):
            response["data"] = data.model_dump()
        # If data is a list of Pydantic models, convert each to a dictionary
        elif isinstance(data, list) and all(isinstance(item, BaseModel) for item in data):
            response["data"] = [item.model_dump() for item in data]
        else:
            # Use custom JSON encoder to handle complex types
            # Filter out Depends objects and other non-serializable types
            serialized = json.loads(json.dumps(data, cls=CustomJSONEncoder))
            # Remove None values that might have been created by filtering
            if isinstance(serialized, dict):
                serialized = {k: v for k, v in serialized.items() if v is not None}
            response["data"] = serialized

    if error is not None:
        response["error"] = error

    return JSONResponse(
        content=response, 
        status_code=status_code, 
        media_type="application/json"
    )
