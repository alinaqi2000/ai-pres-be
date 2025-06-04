from typing import List, Optional, Dict, Any ,Union, Literal
from pydantic import BaseModel, ConfigDict, computed_field
from datetime import datetime
from .image_response import PropertyImageResponse, UnitImageResponse
from enums.unit_type import UnitType
from enums.property_type import PropertyType
from .auth_schema import UserMinimumResponse


class UnitMinimumResponse(BaseModel):
    id: int
    unit_id: Optional[str] = None
    name: str
    unit_type: UnitType
    monthly_rent: float
    images: Optional[List[UnitImageResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class FloorMinimumResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class PropertyMinimumResponse(BaseModel):
    id: int
    property_id: Optional[str] = None
    name: str
    city: str
    address: str
    property_type: PropertyType
    monthly_rent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
    

class UnitResponse(BaseModel):
    id: int
    unit_id: Optional[str] = None
    name: str
    unit_type: UnitType
    area: float
    description: Optional[str]
    monthly_rent: float
    is_occupied: bool
    has_washroom: bool
    has_air_conditioning: bool
    has_internet: bool
    created_at: datetime
    updated_at: Optional[datetime]
    images: Optional[List[UnitImageResponse]] = []

    model_config = ConfigDict(from_attributes=True)


class UnitListResponse(UnitResponse):
    total: int
    property: PropertyMinimumResponse
    floor: FloorMinimumResponse
    unit: UnitMinimumResponse
    model_config = ConfigDict(from_attributes=True)


class FloorResponse(BaseModel):
    id: int
    number: int
    name: Optional[str]
    description: Optional[str] = None
    area: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FloorListResponse(FloorResponse):
    total: int
    units: List[UnitMinimumResponse]

    model_config = ConfigDict(from_attributes=True)


class ItemsResponse(BaseModel):
    item: Union[PropertyMinimumResponse, UnitMinimumResponse]
    type: Literal["property", "unit"]

    model_config = ConfigDict(from_attributes=True)

class PropertyResponse(BaseModel):
    id: int
    property_id: Optional[str] = None
    name: str
    city: str
    address: str
    description: Optional[str]
    total_area: float
    monthly_rent: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None
    property_type: PropertyType
    is_published: bool
    is_occupied: bool    
    thumbnail: Optional[PropertyImageResponse] = None
    images: Optional[List[PropertyImageResponse]] = []
    owner: UserMinimumResponse
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PropertyListResponse(PropertyResponse):
    floors: List[FloorMinimumResponse]
    # units: List[UnitMinimumResponse]
    model_config = ConfigDict(from_attributes=True)
