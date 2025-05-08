from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from enums.invoice_status import InvoiceStatus


class InvoiceBase(BaseModel):
    booking_id: int
    amount: int
    due_date: datetime
    status: InvoiceStatus

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: str) -> InvoiceStatus:
        if isinstance(value, str):
            return InvoiceStatus(value)
        return value


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(InvoiceBase):
    pass


class InvoiceOut(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
