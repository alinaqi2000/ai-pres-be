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
    message: Optional[str] = None
    preferred_move_in: Optional[datetime] = None
    monthly_offer: Optional[int] = None


class TenantRequestCreate(TenantRequestBase):
    tenant_id: int
    property_id: int
    floor_id: int
    unit_id: int

    
class TenantRequestUpdate(BaseModel):
    status: Optional[str] = None
    is_seen: Optional[bool] = None


class TenantRequestOut(TenantRequestBase):
    id: int
    tenant: UserMinimumResponse
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    status: str
    is_seen: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )
