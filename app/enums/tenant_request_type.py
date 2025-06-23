from enum import Enum

class TenantRequestType(str, Enum):
    """Enum for different types of tenant requests"""

    BOOKING = "booking"
    CANCELLATION = "cancellation"
    MAINTENANCE = "maintenance"

    def __str__(self):
        return self.value