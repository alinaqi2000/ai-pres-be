from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.init import Base
from datetime import datetime, timezone


class TenantRequest(Base):
    __tablename__ = "tenant_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    message = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    is_seen = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now(timezone.utc), nullable=True)

    preferred_move_in = Column(DateTime, nullable=True)
    monthly_offer = Column(Integer, nullable=True)
    duration_months = Column(Integer, nullable=True)
    contact_method = Column(String(50), nullable=True)

    tenant = relationship("User", foreign_keys=[tenant_id])
    owner = relationship("User", foreign_keys=[owner_id])
    property = relationship("Property", back_populates="tenant_requests")
    floor = relationship("Floor", back_populates="tenant_requests")
    unit = relationship("Unit", back_populates="tenant_requests")
