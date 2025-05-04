from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UnitBase(BaseModel):
    name: str
    unit_type: str  # 'office', 'shop', 'room'
    area: float
    description: Optional[str] = None
    has_washroom: bool = False
    has_air_conditioning: bool = False
    has_internet: bool = False

class UnitCreate(UnitBase):
    pass

class Unit(UnitBase):
    id: int
    floor_id: int
    created_at: datetime
    updated_at: datetime

class FloorBase(BaseModel):
    number: int
    name: Optional[str] = None
    description: Optional[str] = None
    area: float

class FloorCreate(FloorBase):
    pass

class Floor(FloorBase):
    id: int
    property_id: int
    units: List[Unit] = []
    created_at: datetime
    updated_at: datetime

class PropertyBase(BaseModel):
    name: str
    city: str
    address: str
    description: Optional[str] = None
    total_area: float
    owner_id: Optional[int] = None

class PropertyCreate(PropertyBase):
    pass

class Property(PropertyBase):
    id: int
    floors: List[Floor] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
