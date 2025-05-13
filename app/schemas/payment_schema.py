from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enums.payment_status import PaymentStatus


class PaymentBase(BaseModel):
    booking_id: int
    invoice_id: Optional[int] = None
    amount: float
    payment_method_id: int


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    payment_date: Optional[datetime] = None


class PaymentMinimumResponse(BaseModel):
    id: int
    status: PaymentStatus
    payment_date: Optional[datetime] = None
    transaction_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
