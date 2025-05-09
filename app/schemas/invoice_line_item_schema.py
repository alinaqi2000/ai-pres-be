from pydantic import BaseModel, ConfigDict


class InvoiceLineItemBase(BaseModel):
    description: str
    amount: float


class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass


class InvoiceLineItemOut(InvoiceLineItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
