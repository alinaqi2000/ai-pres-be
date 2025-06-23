from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enums.tenant_request_status import TenantRequestStatus
from enums.tenant_request_type import TenantRequestType

class TenantRequestBase(BaseModel):
    owner_id: Optional[int] = None
    tenant_id: Optional[int] = None
    property_id: Optional[int] = None
    booking_id: Optional[int] = None
    floor_id: Optional[int] = None
    unit_id: Optional[int] = None
    message: Optional[str] = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contact_method: Optional[str] = None
    type: TenantRequestType = TenantRequestType.BOOKING


class TenantRequestCreate(TenantRequestBase):
    pass


class TenantRequestUpdate(BaseModel):
    status: TenantRequestStatus = TenantRequestStatus.PENDING
    is_seen: Optional[bool] = None
            