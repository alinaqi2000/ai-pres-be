from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .property_schema import Property, Floor, Unit


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    city: str

    class Config:
        from_attributes = True


class PropertyResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    description: Optional[str]
    total_area: float
    owner: UserResponse
    created_at: datetime
    updated_at: Optional[datetime]
    floors: List[Floor] = []

    class Config:
        from_attributes = True


class FloorResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]
    description: Optional[str]
    area: float
    property_id: int
    units: List[Unit] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnitResponse(BaseModel):
    id: int
    name: str
    unit_type: str
    area: float
    description: Optional[str]
    has_washroom: bool
    has_air_conditioning: bool
    has_internet: bool
    floor_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    total: int
    items: List[PropertyResponse]

    class Config:
        from_attributes = True
