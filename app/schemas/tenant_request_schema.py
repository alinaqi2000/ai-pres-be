from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class TenantRequestBase(BaseModel):
    owner_id: Optional[int] = None
    tenant_id: Optional[int] = None
    property_id: int
    floor_id: Optional[int] = None
    unit_id: Optional[int] = None
    message: Optional[str] = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None
    duration_months: Optional[int] = None
    contact_method: Optional[str] = None

class TenantRequestCreate(TenantRequestBase):
    pass


class TenantRequestUpdate(BaseModel):
    status: Optional[str] = None
    is_seen: Optional[bool] = None



