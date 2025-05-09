from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from database.init import Base
from enums.payment_status import PaymentStatus 

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True) 
    amount = Column(Float, nullable=False)
    payment_method = Column(String(100), nullable=False) 
    transaction_id = Column(String(255), nullable=True, unique=True) 
    status = Column(SQLAlchemyEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_date = Column(DateTime, nullable=True) 

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = relationship("Booking", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
