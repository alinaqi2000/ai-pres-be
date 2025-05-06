from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ResponseModel(BaseModel):
    status_code: int
    status: str
    message: str
    data: Optional[RoleUpdate] = None
    error: Optional[dict] = None

    updated_at: Optional[datetime]

class RoleOut(RoleBase):
    id: int

    class Config:
        from_attributes = True