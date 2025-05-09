from enum import Enum


class BookingStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment" # If you have a specific state before payment
    PAYMENT_FAILED = "payment_failed"
    PENDING = "pending"  # Pending confirmation or payment
    CONFIRMED = "confirmed"  # Booking confirmed, unit reserved
    ACTIVE = "active"  # Tenant has moved in / booking period is active
    COMPLETED = "completed"  # Booking period ended, tenant moved out
    CANCELLED_BY_TENANT = "cancelled_by_tenant"
    CANCELLED_BY_OWNER = "cancelled_by_owner"
    REJECTED = "rejected"  # If a booking request was rejected
