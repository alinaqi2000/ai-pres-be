from enum import Enum

class InvoiceStatus(str, Enum):
    PAID = "paid"
    OVERDUE = "overdue"
