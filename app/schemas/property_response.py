from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .image_response import PropertyImageResponse, UnitImageResponse

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    city: str

    class Config:
        from_attributes = True

class UnitResponse(BaseModel):
    id: int
    name: str
    unit_type: str
    area: float
    description: Optional[str]
    monthly_rent: float
    is_occupied: bool
    has_washroom: bool
    has_air_conditioning: bool
    has_internet: bool
    floor_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    images: Optional[List[UnitImageResponse]] = []

    class Config:
        from_attributes = True

class FloorResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]
    description: Optional[str]
    area: Optional[float]
    property_id: int
    units: List[UnitResponse] = []
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PropertyResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    description: Optional[str]
    total_area: float
    is_published: bool
    thumbnail: Optional[PropertyImageResponse] = None
    images: Optional[List[PropertyImageResponse]] = []
    owner: UserResponse
    created_at: datetime
    updated_at: Optional[datetime]
    floors: List[FloorResponse] = []

    class Config:
        from_attributes = True

class PropertyListResponse(BaseModel):
    total: int
    items: List[PropertyResponse]

    class Config:
        from_attributes = True

class PropertyMinimumResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True) 


class FloorMinimumResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True) 


class UnitMinimumResponse(BaseModel):    
    id: int
    name: str
    unit_type: str
    area: float
    monthly_rent: float
    images: Optional[List[UnitImageResponse]] = []

    model_config = ConfigDict(from_attributes=True) 
