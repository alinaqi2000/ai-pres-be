from fastapi import APIRouter, Depends
from typing import Annotated

from schemas.user_schema import User
import services.auth_service as auth

router = APIRouter(prefix="/protected", tags=["protected"])

@router.get("/profile")
async def get_profile(current_user: Annotated[User, Depends(auth.get_current_user)]):
    return {"message": "Protected route accessed successfully", "user": current_user}
