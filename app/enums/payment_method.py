from enum import Enum


class PaymentMethodType(str, Enum):
    JAZZCASH = "jazzcash"
    EASYPAISA = "easypaisa"
    CASH = "cash"

class PaymentMethodStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

class PaymentMethodCategory(str, Enum):
    MOBILE_WALLET = "mobile_wallet"
    CASH_PAYMENT = "cash_payment"
