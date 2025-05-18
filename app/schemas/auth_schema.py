from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str
    cnic: Optional[str] = None
    gender: Optional[str] = None
    nature_of_business: Optional[str] = None    

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    cnic: Optional[str] = None
    city: Optional[str] = None
    gender: Optional[str] = None
    nature_of_business: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    city: Optional[str] = None
    cnic: Optional[str] = None
    gender: Optional[str] = None
    nature_of_business: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class ResponseModel(BaseModel):
    status_code: int    
    status: str
    message: str
    data: Optional[Union[Token, UserUpdate]] = None
    error: Optional[dict] = None

class UserMinimumResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    city: str

    class Config:
        from_attributes = True