from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.init import get_db
from schemas.payment_method_schema import PaymentMethodCreate
from schemas.booking_response import PaymentMethodResponse
from services.payment_method_service import (
    service_create_payment_method,
    service_update_payment_method,
    get_payment_method_by_key,
    get_all_payment_methods,
)
from utils.dependencies import get_current_user
from database.models.user_model import User
from responses.success import data_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    bad_request_error,
)
from services.email_service import EmailService

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])
email_service = EmailService()


@router.post("/create-payment-method", response_model=PaymentMethodResponse)
async def route_create_payment_method(
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = service_create_payment_method(db, payment_method)

    if isinstance(result, dict) and "error" in result:
        if "exists" in result["error"].lower():
            return conflict_error(result["error"])
        elif "type" in result["error"].lower() or "category" in result["error"].lower():
            return bad_request_error(result["error"])
        else:
            return internal_server_error(result["error"])

    if current_user.email:
        await email_service.send_create_action_email(
            current_user.email,
            "Payment Method",
            result["id"] if isinstance(result, dict) and "id" in result else None,
        )
    return data_response(result)


@router.get("/get-payment-methods", response_model=List[PaymentMethodResponse])
def read_payment_methods(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    result = get_all_payment_methods(db)

    if isinstance(result, dict) and "error" in result:
        return internal_server_error(result["error"])

    return data_response(result)


@router.get("/{key}", response_model=PaymentMethodResponse)
def read_payment_method(
    key: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user
    result = get_payment_method_by_key(db, key)

    if result is None:
        return not_found_error("Payment method not found")

    return data_response(result)


@router.put("/{key}", response_model=PaymentMethodResponse)
def update_payment_method(
    key: str,
    payment_method: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = service_update_payment_method(db, key, payment_method)

    if isinstance(result, dict) and "error" in result:
        if "not found" in result["error"].lower():
            return not_found_error(f"Payment method with key '{key}' not found")
        elif "type" in result["error"].lower() or "category" in result["error"].lower():
            return bad_request_error(result["error"])
        else:
            return internal_server_error(result["error"])
    return data_response(result)
