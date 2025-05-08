from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import traceback

from database.init import get_db
from schemas.invoice_schema import InvoiceCreate, InvoiceOut, InvoiceUpdate
from services.invoice_service import InvoiceService
from utils.dependencies import get_current_user
from responses.error import not_found_error, internal_server_error
from responses.success import data_response, empty_response
from database.models import User


router = APIRouter(prefix="/invoices", tags=["Invoices"])
invoice_service = InvoiceService()


@router.post("/create_invoice", response_model=InvoiceOut)
def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        return invoice_service.create(db, invoice)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/my_invoices", response_model=List[InvoiceOut])
def read_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        invoices = invoice_service.get_all(db, skip=skip, limit=limit)
        return data_response(
            [InvoiceOut.model_validate(i).model_dump(mode="json") for i in invoices]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{invoice_id}", response_model=InvoiceOut)
def read_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    db_invoice = invoice_service.get(db, invoice_id=invoice_id)
    if db_invoice is None:
        return not_found_error("Invoice not found")
    return db_invoice


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    invoice: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    db_invoice = invoice_service.update(db, invoice_id=invoice_id, invoice=invoice)
    if db_invoice is None:
        return not_found_error("Invoice not found")
    return db_invoice


@router.delete("/{invoice_id}", response_model=InvoiceOut)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    db_invoice = invoice_service.delete(db, invoice_id=invoice_id)
    if db_invoice is None:
        return not_found_error("Invoice not found")
    return empty_response()
