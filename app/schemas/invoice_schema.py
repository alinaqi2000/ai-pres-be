from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from enums.invoice_status import InvoiceStatus
from .invoice_line_item_schema import InvoiceLineItemCreate, InvoiceLineItemOut


class InvoiceBase(BaseModel):
    booking_id: int
    amount: Optional[float] = None
    due_date: datetime
    status: InvoiceStatus


class InvoiceCreate(InvoiceBase):
    line_items: List[InvoiceLineItemCreate]

    model_config = ConfigDict(from_attributes=True)


class InvoiceUpdate(BaseModel):
    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None


class InvoiceMinimumResponse(BaseModel):
    id: int
    status: InvoiceStatus
    amount: Optional[float] = None
    due_date: datetime

    model_config = ConfigDict(from_attributes=True)
