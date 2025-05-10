from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.models.payment_method_model import PaymentMethod
from schemas.payment_method_schema import PaymentMethodCreate
from schemas.booking_response import PaymentMethodResponse
from enums.payment_method import PaymentMethodType, PaymentMethodCategory
from typing import Optional, Union


def service_create_payment_method(
    db: Session, payment_method: PaymentMethodCreate
) -> Union[PaymentMethodResponse, dict]:
    try:
        if payment_method.type not in list(PaymentMethodType):
            return {
                "error": f"Invalid payment method type. Must be one of: {[t.value for t in PaymentMethodType]}"
            }

        if payment_method.category not in list(PaymentMethodCategory):
            return {
                "error": f"Invalid payment method category. Must be one of: {[c.value for c in PaymentMethodCategory]}"
            }

        existing = get_payment_method_by_key(db, payment_method.key)
        if existing:
            return {"error": "Payment method with this key already exists"}

        db_payment_method = PaymentMethod(**payment_method.dict())
        db.add(db_payment_method)
        db.commit()
        db.refresh(db_payment_method)

        return PaymentMethodResponse.from_orm(db_payment_method)
    except IntegrityError:
        db.rollback()
        return {"error": "Duplicate payment method key"}
    except SQLAlchemyError as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"error": f"Unexpected error: {str(e)}"}


def get_payment_method_by_key(db: Session, key: str) -> Optional[PaymentMethodResponse]:
    try:
        db_payment_method = (
            db.query(PaymentMethod).filter(PaymentMethod.key == key).first()
        )
        return (
            PaymentMethodResponse.from_orm(db_payment_method)
            if db_payment_method
            else None
        )
    except SQLAlchemyError as e:
        print(f"Error retrieving payment method: {str(e)}")
        return None


def get_payment_method_model_by_key(db: Session, key: str) -> Optional[PaymentMethod]:
    try:
        return db.query(PaymentMethod).filter(PaymentMethod.key == key).first()
    except SQLAlchemyError as e:
        print(f"Error retrieving payment method: {str(e)}")
        return None


def get_all_payment_methods(db: Session) -> Union[list, dict]:
    try:
        db_payment_methods = db.query(PaymentMethod).all()
        payment_methods = [
            PaymentMethodResponse.from_orm(pm) for pm in db_payment_methods
        ]
        return payment_methods
    except SQLAlchemyError as e:
        return {"error": f"Failed to retrieve payment methods: {str(e)}"}


def get_payment_method_model_for_update(db: Session, key: str) -> Optional[PaymentMethod]:
    try:
        return db.query(PaymentMethod).filter(PaymentMethod.key == key).first()
    except SQLAlchemyError as e:
        print(f"Error retrieving payment method: {str(e)}")
        return None


def service_update_payment_method(db: Session, key: str, payment_method: PaymentMethodCreate) -> Union[PaymentMethodResponse, dict]:
    try:
        if payment_method.type not in list(PaymentMethodType):
            return {"error": f"Invalid payment method type. Must be one of: {[t.value for t in PaymentMethodType]}"}
        
        if payment_method.category not in list(PaymentMethodCategory):
            return {"error": f"Invalid payment method category. Must be one of: {[c.value for c in PaymentMethodCategory]}"}
        
        db_payment_method = get_payment_method_model_by_key(db, key)
        if not db_payment_method:
            return {"error": "Payment method not found"}
        
        # Check if the new key (if changed) already exists
        if payment_method.key and payment_method.key != key:
            existing = get_payment_method_model_by_key(db, payment_method.key)
            if existing:
                return {"error": "A payment method with this key already exists"}
        
        for attr, value in payment_method.dict(exclude_unset=True).items():
            setattr(db_payment_method, attr, value)
        
        db.commit()
        db.refresh(db_payment_method)
        
        return PaymentMethodResponse.from_orm(db_payment_method)
    except IntegrityError as e:
        db.rollback()
        # More specific error handling for integrity constraints
        if 'unique constraint' in str(e).lower():
            return {"error": "Payment method key must be unique"}
        elif 'foreign key constraint' in str(e).lower():
            return {"error": "Invalid reference in payment method"}
        else:
            return {"error": "Update failed due to data integrity issue"}
    except SQLAlchemyError as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"error": f"Unexpected error: {str(e)}"}
