from database.init import Base

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    cnic = Column(String(16), nullable=True)
    gender = Column(String(10), nullable=True)
    phone = Column(String(15), nullable=True)
    nature_of_business = Column(String(100), nullable=True)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    city = Column(String(100), nullable=False)
    booked_by_owner = Column(Boolean, default=False)  # Flag to indicate if user was created by a property owner
    created_by_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # ID of the owner who created this user
    
    search_histories = relationship('SearchHistory', back_populates='user', cascade='all, delete-orphan')
    properties = relationship('Property', back_populates='owner', cascade='all, delete-orphan')
    created_tenants = relationship('User', backref=backref('created_by_owner', remote_side=[id]))
