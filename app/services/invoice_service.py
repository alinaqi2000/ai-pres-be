from sqlalchemy.orm import Session, joinedload
from typing import List
from sqlalchemy import or_
from fastapi import HTTPException
from database.models import Invoice, Booking, Property, User, InvoiceLineItem
from schemas.invoice_schema import InvoiceCreate, InvoiceUpdate

class InvoiceService:
    def __init__(self):
        self.model = Invoice
        self.line_item_model = InvoiceLineItem 

    def get(self, db: Session, invoice_id: int):
        return db.query(self.model).filter(self.model.id == invoice_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def get_for_user(
        self, db: Session, current_user: User, skip: int = 0, limit: int = 100
    ) -> List[Invoice]:
        query = (
            db.query(self.model)
            .join(Invoice.booking)
            .outerjoin(Booking.property)
            .filter(
                or_(
                    Booking.tenant_id == current_user.id,
                    Property.owner_id == current_user.id,
                )
            )
            .options(joinedload(self.model.line_items))
            .distinct()
        )
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, invoice_in: InvoiceCreate) -> Invoice:
        # Check if the booking exists
        booking = db.query(Booking).filter(Booking.id == invoice_in.booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=404, 
                detail=f"Booking with ID {invoice_in.booking_id} not found. Cannot create invoice."
            )

        total_amount = sum(item.amount for item in invoice_in.line_items)

        db_invoice = self.model(
            booking_id=invoice_in.booking_id,
            amount=total_amount, 
            due_date=invoice_in.due_date,
            status=invoice_in.status,
        )
        db.add(db_invoice)
        db.commit() 
        db.refresh(db_invoice)

        for item_in in invoice_in.line_items:
            db_line_item = self.line_item_model(
                **item_in.model_dump(), invoice_id=db_invoice.id
            )
            db.add(db_line_item)
        
        db.commit()  
        db.refresh(db_invoice)  

        db.refresh(db_invoice)
        if not db_invoice.line_items: 
            db_invoice.line_items = db.query(self.line_item_model).filter(self.line_item_model.invoice_id == db_invoice.id).all()

        return db_invoice

    def update(self, db: Session, invoice_id: int, invoice: InvoiceUpdate):
        db_invoice = db.query(self.model).filter(self.model.id == invoice_id).first()
        if db_invoice:
            update_data = invoice.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_invoice, key, value)
            db.commit()
            db.refresh(db_invoice)
        return db_invoice

    def delete(self, db: Session, invoice_id: int):
        db_invoice = db.query(self.model).filter(self.model.id == invoice_id).first()
        if db_invoice:
            db.delete(db_invoice) 
            db.commit()
        return db_invoice
