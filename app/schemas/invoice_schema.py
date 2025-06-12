from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date
from enums.invoice_status import InvoiceStatus
from .invoice_line_item_schema import InvoiceLineItemCreate, InvoiceLineItemResponse


class InvoiceBase(BaseModel):
    booking_id: int
    amount: Optional[float] = None
    due_date: datetime
    status: InvoiceStatus
    reference_number: str
    month: date


class InvoiceCreate(InvoiceBase):
    line_items: List[InvoiceLineItemCreate]

    model_config = ConfigDict(from_attributes=True)


class InvoiceUpdate(BaseModel):
    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None


class InvoiceMinimumResponse(BaseModel):
    id: int
    reference_number: str
    month: date
    status: InvoiceStatus
    amount: Optional[float] = None
    due_date: datetime

    model_config = ConfigDict(from_attributes=True)
