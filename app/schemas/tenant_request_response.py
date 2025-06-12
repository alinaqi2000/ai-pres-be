from .auth_schema import UserMinimumResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enums.tenant_request_status import TenantRequestStatus

from .property_response import (
    PropertyMinimumResponse,
    FloorMinimumResponse,
    UnitMinimumResponse,
)


class TenantRequestMinimumResponse(BaseModel):
    tenant: UserMinimumResponse
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    start_date: datetime
    end_date: datetime
    monthly_offer: Optional[int] = None


    model_config = ConfigDict(from_attributes=True)


class TenantRequestResponse(BaseModel):
    id: int
    tenant: UserMinimumResponse
    owner: UserMinimumResponse
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    start_date: datetime
    end_date: datetime
    monthly_offer: Optional[int] = None
    status: TenantRequestStatus
    is_seen: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
