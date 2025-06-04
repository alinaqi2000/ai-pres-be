from pydantic import BaseModel, Field, ConfigDict
from enums.payment_method import (
    PaymentMethodType,
    PaymentMethodStatus,
    PaymentMethodCategory,
)


class PaymentMethodCreate(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=50, description="Name of the payment method"
    )
    type: PaymentMethodType = Field(..., description="Type of payment method")
    key: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
        description="Unique identifier for the payment method",
    )
    status: PaymentMethodStatus = Field(
        default=PaymentMethodStatus.ACTIVE, description="Status of the payment method"
    )
    category: PaymentMethodCategory = Field(
        default=PaymentMethodCategory.MOBILE_WALLET,
        description="Category of payment method",
    )


class PaymentMethodMinimumResponse(BaseModel):
    name: str
    type: PaymentMethodType
    key: str
    status: PaymentMethodStatus = PaymentMethodStatus.ACTIVE
    category: PaymentMethodCategory = PaymentMethodCategory.MOBILE_WALLET

    model_config = ConfigDict(from_attributes=True)
