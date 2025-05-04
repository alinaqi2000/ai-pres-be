from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enums.unit_type import UnitType

class UnitBase(BaseModel):
    name: str
    unit_type: UnitType
    area: Optional[float] = None
    description: Optional[str] = None
    has_washroom: bool = False
    has_air_conditioning: bool = False
    has_internet: bool = False
    floor_id: Optional[int] = None

class UnitCreate(UnitBase):
    pass

class Unit(UnitBase):
    id: int
    floor_id: int
    created_at: datetime
    updated_at: Optional[datetime]

class FloorBase(BaseModel):
    number: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    area: Optional[float] = None
    property_id: Optional[int] = None

class FloorCreate(FloorBase):
    pass

class Floor(FloorBase):
    id: int
    property_id: int
    units: List[Unit] = []
    created_at: datetime
    updated_at: Optional[datetime]

class PropertyBase(BaseModel):
    name: str
    city: str
    address: str
    description: Optional[str] = None
    total_area: Optional[float] = None
    owner_id: Optional[int] = None

class PropertyCreate(PropertyBase):
    pass

class Property(PropertyBase):
    id: int
    floors: List[Floor] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
