from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base  # Adjust the import based on your project structure


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    price = Column(Float)
    description = Column(String)

    # Add relationship to units
    units = relationship("Unit", back_populates="property", cascade="all, delete")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    unit_number = Column(String, index=True)
    size = Column(Float)
    property_id = Column(Integer, ForeignKey('properties.id'))

    # Add relationship to property
    property = relationship("Property", back_populates="units")

    # ...existing code...