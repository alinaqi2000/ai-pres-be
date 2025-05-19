from .auth_schema import UserMinimumResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

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
    monthly_offer: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TenantRequestResponse(BaseModel):
    id: int
    tenant: UserMinimumResponse
    owner: UserMinimumResponse
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    status: str
    is_seen: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
