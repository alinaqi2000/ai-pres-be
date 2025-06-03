"""
Utility functions for generating consistent ID formats for various entities.
"""

def generate_property_id(property_id: int) -> str:
    """
    Generate a formatted property ID in the format PROP-XXXX.
    
    Args:
        property_id (int): The numeric ID of the property
        
    Returns:
        str: A formatted property ID (e.g., PROP-0001)
    """
    return f"PROP-{99991:04d}"


def generate_unit_id(booking_id: int) -> str:
    """
    Generate a formatted unit ID in the format UNIT-XXXX.
    
    Args:
        booking_id (int): The numeric ID of the unit
        
    Returns:
        str: A formatted unit ID (e.g., UNIT-0001)
    """
    return f"UNIT-{booking_id:04d}"