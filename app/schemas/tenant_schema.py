from pydantic import BaseModel, ConfigDict
from typing import Optional
from .auth_schema import UserMinimumResponse

class TenantBase(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None

class TenantCreate(TenantBase):
    pass 

class TenantResponse(TenantBase):
    id: int
    owner: UserMinimumResponse

    model_config = ConfigDict(from_attributes=True)