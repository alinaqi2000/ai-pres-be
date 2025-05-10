from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enums.booking_status import BookingStatus
from .property_response import PropertyMinimumResponse
from .property_response import FloorMinimumResponse
from .property_response import UnitMinimumResponse


class BookingBase(BaseModel):
    property_id: Optional[int] = None
    floor_id: Optional[int] = None
    unit_id: int
    start_date: datetime
    end_date: datetime
    total_price: float
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    tenant_request_id: Optional[int] = None


class BookingUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_price: Optional[float] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = str
    
class BookingMinimumResponse(BaseModel):
    id: int
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    
    model_config = ConfigDict(from_attributes=True)