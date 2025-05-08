from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PropertyImageBase(BaseModel):
    property_id: int
    image_path: str
    is_thumbnail: bool = False


class PropertyImageCreate(PropertyImageBase):
    pass


class PropertyImage(PropertyImageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        model_config = {"from_attributes": True}


class UnitImageBase(BaseModel):
    unit_id: int
    image_path: str


class UnitImageCreate(UnitImageBase):
    pass


class UnitImage(UnitImageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        model_config = {"from_attributes": True}
