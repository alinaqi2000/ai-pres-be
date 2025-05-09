from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.models.payment_model import Payment
from database.models.booking_model import Booking
from database.models.invoice_model import Invoice
from schemas.payment_schema import PaymentCreate, PaymentUpdate
from enums.payment_status import PaymentStatus
from enums.booking_status import BookingStatus


class PaymentService:
    def get_payment(self, db: Session, payment_id: int) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.id == payment_id).first()

    def create_payment(
        self, db: Session, payment_in: PaymentCreate, user_id: int
    ) -> Payment:
        booking = db.query(Booking).filter(Booking.id == payment_in.booking_id).first()
        if not booking or booking.tenant_id != user_id:
            raise ValueError("Invalid booking or user not authorized for this booking.")

        if payment_in.invoice_id:
            invoice = (
                db.query(Invoice).filter(Invoice.id == payment_in.invoice_id).first()
            )
            if not invoice or invoice.booking_id != payment_in.booking_id:
                raise ValueError("Invalid invoice or invoices does not match booking.")
            if invoice.amount != payment_in.amount:
                pass
        db_payment = Payment(**payment_in.model_dump(), status=PaymentStatus.PENDING)
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def update_payment(
        self, db: Session, payment_id: int, payment_update: PaymentUpdate
    ) -> Optional[Payment]:
        db_payment = self.get_payment(db, payment_id)
        if not db_payment:
            return None

        update_data = payment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_payment, key, value)

        db_payment.updated_at = datetime.now()
        db.commit()
        db.refresh(db_payment)

        if db_payment.status == PaymentStatus.COMPLETED:
            booking = (
                db.query(Booking).filter(Booking.id == db_payment.booking_id).first()
            )
            if booking:
                if (
                    booking.status == BookingStatus.PENDING_PAYMENT
                    or booking.status == BookingStatus.PENDING
                ):
                    booking.status = BookingStatus.CONFIRMED
                    booking.updated_at = datetime.now()
                    db.commit()
                    db.refresh(booking)
        elif db_payment.status == PaymentStatus.FAILED:
            booking = (
                db.query(Booking).filter(Booking.id == db_payment.booking_id).first()
            )
            if booking and booking.status not in [
                BookingStatus.CANCELLED,
                BookingStatus.COMPLETED,
            ]:
                booking.status = BookingStatus.PAYMENT_FAILED
                booking.updated_at = datetime.now()
                db.commit()
                db.refresh(booking)

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
        return (
            db.query(Payment)
            .join(Payment.booking)
            .filter(Booking.tenant_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
