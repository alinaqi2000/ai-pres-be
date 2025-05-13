from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.init import Base 

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True)
    phone_number = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id")) 

    owner = relationship("User", back_populates="tenants")
    bookings = relationship("Booking", back_populates="tenant")
