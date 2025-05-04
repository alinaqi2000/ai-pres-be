from pydantic import BaseModel, computed_field, Field
from config import BASE_URL

class PropertyImageResponse(BaseModel):
    id: int
    image_path: str = Field(..., exclude=True)

    @computed_field
    @property
    def image_url(self) -> str:
        return f"{BASE_URL}/{self.image_path}"

    class Config:
        from_attributes = True

class UnitImageResponse(BaseModel):
    id: int
    image_path: str = Field(..., exclude=True)
    
    @computed_field
    @property
    def image_url(self) -> str:
        return f"{BASE_URL}/{self.image_path}"

    class Config:
        from_attributes = True
