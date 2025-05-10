from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enums.booking_status import BookingStatus
from enums.payment_method import PaymentMethodType, PaymentMethodStatus, PaymentMethodCategory
from .invoice_schema import InvoiceLineItemOut
from .auth_schema import UserMinimumResponse
from .tenant_request_schema import TenantRequestMinimumResponse
from .property_response import PropertyMinimumResponse
from .property_response import FloorMinimumResponse
from .property_response import UnitMinimumResponse
from .booking_schema import BookingMinimumResponse
from enums.payment_status import PaymentStatus
from .invoice_schema import InvoiceMinimumResponse
from .payment_method_schema import PaymentMethodMinimumResponse


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


class BookingResponse(BaseModel):
    id: int
    tenant: UserMinimumResponse
    tenant_request: TenantRequestMinimumResponse
    status: BookingStatus
    payment_method: Optional[PaymentMethodMinimumResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: int
    booking: BookingMinimumResponse
    line_items: List[InvoiceLineItemOut] = []
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



    