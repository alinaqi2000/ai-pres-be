from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from ..init import Base
from enums.payment_method import PaymentMethodType, PaymentMethodStatus, PaymentMethodCategory

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    type = Column(Enum(PaymentMethodType), index=True)
    key = Column(String(100), unique=True, index=True)
    status = Column(Enum(PaymentMethodStatus), default=PaymentMethodStatus.ACTIVE)
    category = Column(Enum(PaymentMethodCategory), nullable=True)
    
    # Relationship with payments
    payments = relationship('Payment', back_populates='payment_method', cascade='all, delete-orphan')