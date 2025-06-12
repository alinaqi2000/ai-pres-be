from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enums.tenant_request_status import TenantRequestStatus

class TenantRequestBase(BaseModel):
    owner_id: Optional[int] = None
    tenant_id: Optional[int] = None
    property_id: int
    floor_id: int = None
    unit_id: int = None
    message: str = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    contact_method: Optional[str] = None


class TenantRequestCreate(TenantRequestBase):
    pass


class TenantRequestUpdate(BaseModel):
    status: TenantRequestStatus = str
    is_seen: Optional[bool] = None
            