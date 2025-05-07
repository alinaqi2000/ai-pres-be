from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from database.init import Base
from enums.booking_status import BookingStatus  # Import the enum


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), default=BookingStatus.PENDING.value, nullable=False)
    notes = Column(Text, nullable=True)  # Optional notes from tenant or owner

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    tenant = relationship("User")
    property = relationship("Property")
    floor = relationship("Floor")
    unit = relationship("Unit")

    # Add back_populates if you intend to have these relationships accessible
    # from the other side (e.g., user.bookings, property.bookings)
    # Example for Property (assuming Property model has a 'bookings' relationship defined):
    # property = relationship("Property", back_populates="bookings")
