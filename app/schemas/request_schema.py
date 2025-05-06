from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TenantRequestBase(BaseModel):
    message: Optional[str] = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None

class TenantRequestCreate(TenantRequestBase):
    tenant_id: int
    property_id: int

class TenantRequestUpdate(BaseModel):
    status: Optional[str] = None
    is_seen: Optional[bool] = None

class TenantRequestOut(TenantRequestBase):
    id: int
    tenant_id: int
    property_id: int
    status: str
    is_seen: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
