from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union

from .role_schema import RoleOut


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    roles: List[RoleOut] = []

    class Config:
        orm_mode = True
        from_attributes = True


class ResponseModel(BaseModel):
    status_code: int
    status: str
    message: str
    data: Optional[Union[Token, UserUpdate]] = None
    error: Optional[dict] = None
