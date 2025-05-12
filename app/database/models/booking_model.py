from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..init import Base
from enums.booking_status import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    tenant_request_id = Column(Integer, ForeignKey("tenant_requests.id"), nullable=False)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), default=BookingStatus.PENDING.value, nullable=False)
    notes = Column(Text, nullable=True)  

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=datetime.now(timezone.utc), nullable=True)

    tenant = relationship("User")
    property = relationship("Property")
    floor = relationship("Floor")
    unit = relationship("Unit")
    tenant_request = relationship("TenantRequest")
    payments = relationship("Payment", back_populates="booking")
    invoices = relationship("Invoice", back_populates="booking")
