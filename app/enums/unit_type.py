from enum import Enum


class UnitType(str, Enum):
    """Enum for different types of units"""

    OFFICE = "office"
    SHOP = "shop"
    ROOM = "room"

    def __str__(self):
        return self.value
