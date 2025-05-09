from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enums.booking_status import BookingStatus
from .invoice_schema import InvoiceLineItemOut
from .auth_schema import UserMinimumResponse
from .tenant_request_schema import TenantRequestMinimumResponse
from .property_response import PropertyMinimumResponse
from .property_response import FloorMinimumResponse
from .property_response import UnitMinimumResponse
from .booking_schema import BookingMinimumResponse
from enums.payment_status import PaymentStatus
from .invoice_schema import InvoiceMinimumResponse


class TenantRequestOut(BaseModel):
    id: int
    tenant: UserMinimumResponse
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    status: str
    is_seen: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BookingOut(BaseModel):
    id: int
    tenant: UserMinimumResponse
    tenant_request: TenantRequestMinimumResponse
    status: BookingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceOut(BaseModel):
    id: int
    booking: BookingMinimumResponse
    line_items: List[InvoiceLineItemOut] = []
    amount: float
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PaymentOut(BaseModel):
    id: int
    invoice: InvoiceMinimumResponse
    transaction_id: Optional[str] = None
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
