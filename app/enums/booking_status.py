from enum import Enum


class BookingStatus(str, Enum):
    ACTIVE = "active"
    # PENDING = "pending"
    CLOSED = "closed"
