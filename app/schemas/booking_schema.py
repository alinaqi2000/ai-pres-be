from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enums.booking_status import BookingStatus


class BookingBase(BaseModel):
    property_id: int
    floor_id: int
    unit_id: int
    start_date: datetime
    end_date: datetime
    total_price: float
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_price: Optional[float] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingOut(BookingBase):
    id: int
    tenant_id: int
    status: BookingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = str
