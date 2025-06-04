from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import or_
from fastapi import HTTPException
from database.models import Invoice, Booking, Property, User, InvoiceLineItem
from schemas.invoice_schema import InvoiceCreate, InvoiceUpdate, InvoiceLineItemCreate
from datetime import timedelta


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
        booking = db.query(Booking).filter(Booking.id == invoice_in.booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=404,
                detail=f"Booking with ID {invoice_in.booking_id} not found. Cannot create invoice.",
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
            db_invoice.line_items = (
                db.query(self.line_item_model)
                .filter(self.line_item_model.invoice_id == db_invoice.id)
                .all()
            )

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
        db_invoice = (
            db.query(self.model)
            .options(joinedload(self.model.booking))
            .filter(self.model.id == invoice_id)
            .first()
        )
        if db_invoice:
            _ = db_invoice.booking
            db.delete(db_invoice)
            db.commit()
        return db_invoice

    def create_invoice_from_booking(self, db: Session, booking: Booking) -> Optional[Invoice]:
        """Create an invoice automatically when a booking is confirmed"""
        try:
            # Create line item for booking
            line_item = InvoiceLineItemCreate(
                description=f"Booking payment for {booking.start_date.date()} to {booking.end_date.date()}",
                amount=booking.total_price,
                quantity=1
            )

            # Set due date to 7 days before booking start
            due_date = booking.start_date - timedelta(weeks=4)

            # Create invoice data
            invoice_data = InvoiceCreate(
                booking_id=booking.id,
                due_date=due_date,
                status="pending",
                line_items=[line_item]
            )

            return self.create(db, invoice_data)
        except Exception as e:
            print(f"Error creating invoice from booking: {str(e)}")
            return None

    def get_tenant_invoices(self, db: Session, tenant_id: int, property_owner_id: int) -> List[Invoice]:
        """Get all invoices for a specific tenant, only accessible by property owner"""
        return (
            db.query(self.model)
            .join(Invoice.booking)
            .join(Booking.property)
            .filter(
                Booking.tenant_id == tenant_id,
                Property.owner_id == property_owner_id
            )
            .options(joinedload(self.model.line_items))
            .all()
        )

