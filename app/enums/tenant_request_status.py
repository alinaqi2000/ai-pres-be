from enum import Enum

class TenantRequestStatus(str, Enum):
    """Enum for different statuses of tenant requests"""

    PENDING = "pending"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

    def __str__(self):
        return self.value