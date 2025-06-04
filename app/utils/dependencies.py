from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional

from database.init import get_db
from database.models.user_model import User
from config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

from responses.error import unauthorized_error, not_found_error

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid provided token")
    
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


def is_owner(user: User, db: Session) -> bool:
    """Check if a user is a property owner by seeing if they have any properties"""
    from database.models.property_model import Property
    
    property_count = db.query(Property).filter(Property.owner_id == user.id).count()
    return property_count > 0


def is_tenant(user: User, db: Session) -> bool:
    """Check if a user is a tenant by seeing if they have any bookings"""
    from database.models.booking_model import Booking
    
    booking_count = db.query(Booking).filter(Booking.tenant_id == user.id).count()
    return booking_count > 0


def owner_required(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dependency to ensure the current user is a property owner"""
    if not is_owner(current_user, db):
        raise HTTPException(status_code=403, detail="Only property owners can access this endpoint")
    return current_user


def tenant_required(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dependency to ensure the current user is a tenant"""
    if not is_tenant(current_user, db):
        raise HTTPException(status_code=403, detail="Only tenants can access this endpoint")
    return current_user
