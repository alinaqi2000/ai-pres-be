from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.init import Base


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)  # Using Float for monetary values

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    invoice = relationship("Invoice", back_populates="line_items")

    def __repr__(self):
        return f"<InvoiceLineItem(id={self.id}, description='{self.description}', amount={self.amount})>"
