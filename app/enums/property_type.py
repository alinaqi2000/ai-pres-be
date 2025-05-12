from enum import Enum


class PropertyType(str, Enum):
    """Enum for different types of properties"""

    BUILDING = "building"
    HOUSE = "house"
    APARTMENT = "apartment"

    def __str__(self):
        return self.value
