from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    roles: List[RoleBase]

    class Config:
        orm_mode = True
