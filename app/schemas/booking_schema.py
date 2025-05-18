from pydantic import BaseModel, ConfigDict  # Removed model_validator import
from typing import Optional
from datetime import datetime
from enums.booking_status import BookingStatus
from .property_response import PropertyMinimumResponse
from enums.property_type import PropertyType
from .property_response import FloorMinimumResponse
from .property_response import UnitMinimumResponse

class BookingBase(BaseModel):
    property_id: Optional[int] = None
    floor_id: Optional[int] = None
    unit_id: Optional[int] = None
    start_date: datetime
    end_date: datetime
    total_price: float
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    tenant_id: Optional[int] = None
    tenant_request_id: Optional[int] = None


class BookingUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tenant_id: Optional[int] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = str


class BookingPropertyResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    property_type: PropertyType

    model_config = ConfigDict(from_attributes=True)


class BookingFloorResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BookingMinimumResponse(BaseModel):
    id: int
    booked_by_owner: bool
    start_date: datetime
    end_date: datetime
    property: Optional[PropertyMinimumResponse] = None
    floor: Optional[FloorMinimumResponse] = None
    unit: Optional[UnitMinimumResponse] = None
  

    model_config = ConfigDict(from_attributes=True)
