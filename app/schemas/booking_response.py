from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enums.booking_status import BookingStatus
from enums.payment_method import (
    PaymentMethodType,
    PaymentMethodStatus,
    PaymentMethodCategory,
)
from .invoice_schema import InvoiceLineItemResponse
from .tenant_request_response import TenantRequestMinimumResponse
from .booking_schema import BookingMinimumResponse
from enums.payment_status import PaymentStatus
from .invoice_schema import InvoiceMinimumResponse
from .payment_method_schema import PaymentMethodMinimumResponse
from .auth_schema import UserMinimumResponse
from .property_response import PropertyMinimumResponse
from .property_response import FloorMinimumResponse
from .property_response import UnitMinimumResponse
from enums.invoice_status import InvoiceStatus

class BookingResponse(BaseModel):
    id: int
    tenant: Optional[UserMinimumResponse] = None
    owner: Optional[UserMinimumResponse] = None
    property: Optional[PropertyMinimumResponse] = None
    floor: Optional[FloorMinimumResponse] = None  # Will be populated for tenant request bookings
    unit: Optional[UnitMinimumResponse] = None# Will be populated for tenant request bookings
    booked_by_owner: bool
    status: BookingStatus
    created_at: datetime
    start_date: datetime        
    end_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
    total_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: int
    tenant: Optional[UserMinimumResponse] = None
    owner: Optional[UserMinimumResponse] = None
    booking: BookingMinimumResponse
    status: InvoiceStatus
    line_items: List[InvoiceLineItemResponse] = []
    reference_number: str
    month: datetime
    amount: float
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: int
    invoice: InvoiceMinimumResponse
    transaction_id: Optional[str] = None
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    payment_method: Optional[PaymentMethodMinimumResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentMethodResponse(BaseModel):
    id: int
    name: str
    type: PaymentMethodType
    key: str
    status: PaymentMethodStatus = PaymentMethodStatus.ACTIVE
    category: PaymentMethodCategory = PaymentMethodCategory.MOBILE_WALLET

    model_config = ConfigDict(from_attributes=True)
