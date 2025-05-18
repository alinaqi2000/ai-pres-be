from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse 
from sqlalchemy.orm import Session
from typing import List

from database.init import get_db
from database.models.user_model import User
from database.models.property_model import Property
from database.models.booking_model import Booking
from database.models.invoice_model import Invoice
from schemas.payment_schema import PaymentCreate, PaymentUpdate
from schemas.booking_response import PaymentResponse
from services.email_service import EmailService
from services.payment_service import PaymentService
from utils.dependencies import get_current_user
from responses.success import data_response
from responses.error import (
    not_found_error,
    conflict_error,
    forbidden_error,
    internal_server_error,
)
import traceback

router = APIRouter(prefix="/payments", tags=["Payments"])
payment_service = PaymentService()
email_service = EmailService()

@router.post("/create_payment", response_model=PaymentResponse)
async def create_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),):
    if not isinstance(current_user, User):
        return current_user
    try:
        created_payment_result = payment_service.create_payment(
            db, payment_in, current_user.id
        )

        if isinstance(created_payment_result, JSONResponse):
            return created_payment_result

        created_payment = created_payment_result
        # Send email notification for payment creation
        email_service = EmailService()
        if current_user.email:
            await email_service.send_create_action_email(current_user.email, "Payment", created_payment.id)
        return data_response(
            PaymentResponse.model_validate(created_payment).model_dump(mode="json")
        )
    except HTTPException as he:
        raise he
    except ValueError as ve: 
        traceback.print_exc()
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),):
    if not isinstance(current_user, User):
        return current_user
    try:
        payment = payment_service.get_payment(db, payment_id)
        if not payment:
            return not_found_error(f"Payment with ID {payment_id} not found.")

        booking = payment.booking
        if not booking:
            return internal_server_error("Booking data associated with payment is missing.")

        is_tenant = booking.tenant_id == current_user.id

        property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
        if not property_obj:
            return internal_server_error(
                "Property data associated with booking is missing."
            )

        is_owner = property_obj.owner_id == current_user.id

        if not (is_tenant or is_owner):
            return forbidden_error("Not authorized to view this payment.")

        return data_response(PaymentResponse.model_validate(payment).model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),):
    if not isinstance(current_user, User):
        return current_user
    try:
        payment_to_check = payment_service.get_payment(db, payment_id)
        if not payment_to_check:
            return not_found_error(f"Payment with ID {payment_id} not found to check authorization.")
        if isinstance(payment_to_check, JSONResponse):
             return payment_to_check

        booking_of_payment = db.query(Booking).filter(Booking.id == payment_to_check.booking_id).first()
        if not booking_of_payment:
            return internal_server_error("Booking associated with payment not found.")

        property_of_booking = db.query(Property).filter(Property.id == booking_of_payment.property_id).first()
        if not property_of_booking:
            return internal_server_error("Property associated with booking not found.")

        if property_of_booking.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this payment. Only property owner can update.")

        updated_payment_result = payment_service.update_payment(
            db, payment_id, payment_update
        )

        if isinstance(updated_payment_result, JSONResponse):
            return updated_payment_result
        
        # Send email notification for payment update
        from services.email_service import EmailService
        email_service = EmailService()
        if current_user.email:
            await email_service.send_update_action_email(current_user.email, "Payment", payment_id)
        return data_response(
            PaymentResponse.model_validate(updated_payment_result).model_dump(mode="json")
        )
    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/booking/{booking_id}", response_model=List[PaymentResponse])
def get_payments_for_booking_route(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),    skip: int = 0,
    limit: int = 100,
):
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        is_tenant = booking.tenant_id == current_user.id

        property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
        if not property_obj:
            return internal_server_error("Property associated with booking not found.")

        is_owner = property_obj.owner_id == current_user.id

        if not (is_tenant or is_owner):
            return forbidden_error("Not authorized to view payments for this booking.")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

    payments = payment_service.get_payments_for_booking(db, booking_id, skip, limit)
    return data_response(
        [PaymentResponse.model_validate(p).model_dump(mode="json") for p in payments]
    )


@router.get("/invoice/{invoice_id}", response_model=List[PaymentResponse])
def get_payments_for_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),    skip: int = 0,
    limit: int = 100,
):
    if not isinstance(current_user, User):
        return current_user
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return not_found_error(f"Invoice with ID {invoice_id} not found.")

        if not invoice.booking:
            return internal_server_error("Booking associated with invoice not found.")

        is_tenant = invoice.booking.tenant_id == current_user.id

        property_obj = (
            db.query(Property).filter(Property.id == invoice.booking.property_id).first()
        )
        if not property_obj:
            return internal_server_error(
                "Property associated with invoice's booking not found."
            )

        is_owner = property_obj.owner_id == current_user.id

        if not (is_tenant or is_owner):
            return forbidden_error("Not authorized to view payments for this invoice.")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

    payments = payment_service.get_payments_for_invoice(db, invoice_id, skip, limit)
    return data_response(
        [PaymentResponse.model_validate(p).model_dump(mode="json") for p in payments]
    )


@router.get("/user/me", response_model=List[PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),    skip: int = 0,
    limit: int = 100,
):
    if not isinstance(current_user, User):
        return current_user
    try:
        payments = payment_service.get_payments_by_user(db, current_user.id, skip, limit)
        return data_response(
            [PaymentResponse.model_validate(p).model_dump(mode="json") for p in payments]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
