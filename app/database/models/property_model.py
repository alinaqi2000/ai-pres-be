from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.init import Base

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    unit_type = Column(String(100))  # 'office', 'shop', 'room'
    area = Column(Float)
    description = Column(String(2000), nullable=True)
    has_washroom = Column(Boolean, default=False)
    has_air_conditioning = Column(Boolean, default=False)
    has_internet = Column(Boolean, default=False)
    floor_id = Column(Integer, ForeignKey("floors.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer)
    name = Column(String(100), nullable=True)
    description = Column(String(2000), nullable=True)
    area = Column(Float)
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    units = relationship("Unit", backref="floor")
    property = relationship("Property", back_populates="floors")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    city = Column(String(100))
    address = Column(String(255))
    description = Column(String(2000), nullable=True)
    total_area = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    floors = relationship("Floor", back_populates="property")
    owner = relationship("User")
