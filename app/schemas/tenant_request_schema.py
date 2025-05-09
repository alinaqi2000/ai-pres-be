from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from .property_response import (
    UnitMinimumResponse,
    FloorMinimumResponse,
    PropertyMinimumResponse,
)
from .auth_schema import UserMinimumResponse


class TenantRequestBase(BaseModel):
    tenant_id: Optional[int] = None
    property_id: int
    floor_id: int
    unit_id: int
    message: Optional[str] = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None


class TenantRequestCreate(TenantRequestBase):
    pass


class TenantRequestUpdate(BaseModel):
    status: Optional[str] = None
    is_seen: Optional[bool] = None


class TenantRequestMinimumResponse(BaseModel):
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    monthly_offer: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
