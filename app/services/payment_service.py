from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.models.payment_model import Payment
from database.models.booking_model import Booking
from database.models.invoice_model import Invoice
from database.models.property_model import Property, Unit
from schemas.payment_schema import PaymentCreate, PaymentUpdate
from enums.payment_status import PaymentStatus
from enums.booking_status import BookingStatus
from responses.error import not_found_error


class PaymentService:
    def get_payment(self, db: Session, payment_id: int) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.id == payment_id).first()

    def create_payment(
        self, db: Session, payment_in: PaymentCreate, user_id: int
    ) -> Payment:
        if not payment_in.invoice_id:
            return not_found_error("Invoice ID is required.")

        invoice = db.query(Invoice).filter(Invoice.id == payment_in.invoice_id).first()
        if not invoice:
            return not_found_error("Invalid invoice ID.")

        # Get booking and check authorization
        booking = db.query(Booking).filter(Booking.id == invoice.booking_id).first()
        if not booking:
            return not_found_error("Invoice has no associated booking.")

        # Check if user is authorized
        authorized_to_pay = False
        if booking.tenant_id == user_id:
            authorized_to_pay = True
        elif booking.property_id:
            property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
            if property_obj and property_obj.owner_id == user_id:
                authorized_to_pay = True

        if not authorized_to_pay:
            return not_found_error("User not authorized to make payment for this invoice.")

        # Validate payment amount matches invoice
        if invoice.amount != payment_in.amount:
            return not_found_error("Payment amount must match invoice amount.")

        # Create payment with booking_id from invoice
        db_payment = Payment(
            **payment_in.model_dump(),
            booking_id=invoice.booking_id,
            status=PaymentStatus.PENDING
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def update_payment(
        self, db: Session, payment_id: int, payment_update: PaymentUpdate
    ) -> Optional[Payment]:
        db_payment = self.get_payment(db, payment_id)
        if not db_payment:
            return not_found_error("Payment not found.")

        update_data = payment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment, key, value)

        db_payment.updated_at = datetime.now()
        db.commit()
        db.refresh(db_payment)

        # if db_payment.status == PaymentStatus.COMPLETED:
        #     booking = (
        #         db.query(Booking).filter(Booking.id == db_payment.booking_id).first()
        #     )
        #     booking.status = BookingStatus.CONFIRMED
        #     booking.updated_at = datetime.now()
        #     db.commit()
        #     db.refresh(booking)
        # elif db_payment.status == PaymentStatus.FAILED:
        #     booking = (
        #         db.query(Booking).filter(Booking.id == db_payment.booking_id).first()
        #     )
        #     if booking and booking.status not in [
        #         BookingStatus.CANCELLED,
        #         BookingStatus.COMPLETED,
        #     ]:
        #         booking.status = BookingStatus.PENDING
        #         booking.updated_at = datetime.now()
        #         db.commit()
        #         db.refresh(booking)

        return db_payment

    def get_payments_for_booking(
        self, db: Session, booking_id: int, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.booking_id == booking_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_payments_for_invoice(
        self, db: Session, invoice_id: int, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.invoice_id == invoice_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_payments_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        tenant_payments = (
            db.query(Payment)
            .join(Payment.booking)
            .filter(Booking.tenant_id == user_id)
            .all()
        )

        owner_payments = (
            db.query(Payment)
            .join(Payment.booking)
            .join(Booking.property)
            .filter(Property.owner_id == user_id)
            .all()
        )

        all_payments = tenant_payments + owner_payments
        return all_payments[skip : skip + limit]
