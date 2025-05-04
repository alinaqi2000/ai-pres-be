from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.init import Base
from enums.unit_type import UnitType

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    unit_type = Column(Enum(UnitType))
    area = Column(Float, nullable=True)
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
    area = Column(Float, nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    units = relationship("Unit", backref="floor", cascade="all, delete-orphan")
    property = relationship("Property", back_populates="floors")

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    city = Column(String(100))
    address = Column(String(255))
    description = Column(String(2000), nullable=True)
    total_area = Column(Float, nullable=True)
    is_published = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    floors = relationship("Floor", back_populates="property", cascade="all, delete-orphan")
    owner = relationship("User")
