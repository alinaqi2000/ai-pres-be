from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enums.unit_type import UnitType
from enums.property_type import PropertyType


class UnitBase(BaseModel):
    name: str
    unit_type: UnitType
    area: Optional[float] = None
    description: Optional[str] = None
    monthly_rent: int
    is_occupied: bool
    has_washroom: bool = False
    has_air_conditioning: bool = False
    has_internet: bool = False
    floor_id: Optional[int] = None
    property_id: Optional[int] = None


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
    property_type: PropertyType
    address: str
    description: Optional[str] = None
    total_area: Optional[float] = None
    monthly_rent: Optional[float] = None
    is_published: bool = False
    owner_id: Optional[int] = None
    is_occupied: bool 


class PropertyCreate(PropertyBase):
    is_published: Optional[bool] = None


class Property(PropertyBase):
    id: int
    floors: List[Floor] = []
    created_at: datetime
    updated_at: Optional[datetime]
    is_published: bool = False

    class Config:
        from_attributes = True
        model_config = {"from_attributes": True}
