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
    return f"PROP-{property_id:04d}"
