from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.init import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    amount = Column(Float)  # Changed from Integer to Float
    due_date = Column(DateTime, default=datetime.now())
    status = Column(String(20))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    booking = relationship("Booking")
    line_items = relationship(
        "InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice(id={self.id})>"
