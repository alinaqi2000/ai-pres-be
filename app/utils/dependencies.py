from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database.init import get_db
from models.user_model import User
from config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

from responses.error import (
    unauthorized_error,
    not_found_error
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------ Hashing and Verify Password ------------------


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ------------------ Create Access Token ------------------


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------ GET Current User ------------------


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return unauthorized_error("Invalid credentials")
    except JWTError:
        return unauthorized_error("Invalid provided token")
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        return not_found_error("User not found")
    return user
