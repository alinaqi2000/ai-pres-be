from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List
import traceback
import asyncio

from database.init import get_db
from database.models import TenantRequest, Invoice, Property, User
from schemas.invoice_schema import InvoiceCreate, InvoiceUpdate
from schemas.booking_response import BookingMinimumResponse, InvoiceResponse
from schemas.property_response import (
    PropertyMinimumResponse,
    FloorMinimumResponse,
    UnitMinimumResponse,
)
from services.invoice_service import InvoiceService
from utils.dependencies import get_current_user
from utils import generate_property_id
from responses.error import not_found_error, internal_server_error, forbidden_error
from responses.success import data_response, empty_response
from schemas.auth_schema import UserMinimumResponse
from services.email_service import EmailService


router = APIRouter(prefix="/invoices", tags=["Invoices"])
invoice_service = InvoiceService()

# Helper function to format invoice responses consistently
def format_invoice_response(db, invoice):
    """
    Format an invoice into a consistent InvoiceResponse object with properly formatted
    booking, property, and tenant information.
    
    Args:
        db: Database session
        invoice: The invoice object to format
        
    Returns:
        A formatted InvoiceResponse object ready for response
    """
    response = InvoiceResponse.model_validate(invoice)
    booking = invoice.booking
    
    if not booking:
        return response
        
    # Setup booking response
    booking_data = BookingMinimumResponse.model_validate(booking).model_dump(mode="json")
    
    # Add tenant information
    if booking.tenant_id:
        tenant_user = db.query(User).filter(User.id == booking.tenant_id).first()
        if tenant_user:
            response.tenant = UserMinimumResponse.model_validate(tenant_user)
    
    # Ensure property_id is properly formatted for booking properties
    if 'property' in booking_data and booking_data['property'] and 'id' in booking_data['property']:
        if 'property_id' not in booking_data['property'] or not booking_data['property']['property_id']:
            booking_data['property']['property_id'] = generate_property_id(booking_data['property']['id'])
    
    # Get tenant request information if it exists
    tenant_request = None
    if hasattr(booking, "tenant_request_id") and booking.tenant_request_id:
        tenant_request = db.query(TenantRequest).filter(TenantRequest.id == booking.tenant_request_id).first()
        
        # If tenant isn't set but we have a tenant request, use the tenant from there
        if tenant_request and not response.tenant and tenant_request.tenant_id:
            tenant_user = db.query(User).filter(User.id == tenant_request.tenant_id).first()
            if tenant_user:
                response.tenant = UserMinimumResponse.model_validate(tenant_user)
            
        # If we have property info from the booking, don't duplicate it from tenant request
        if tenant_request and 'property' not in booking_data:
            # Create property response with properly formatted property_id
            property_response = PropertyMinimumResponse.model_validate(tenant_request.property)
            
            # Ensure property_id is formatted correctly
            if not property_response.property_id:
                property_response.property_id = generate_property_id(tenant_request.property.id)
                
            booking_data["property"] = property_response.model_dump(mode="json")
            booking_data["floor"] = (
                FloorMinimumResponse.model_validate(tenant_request.floor).model_dump(mode="json")
                if tenant_request.floor
                else None
            )
            booking_data["unit"] = (
                UnitMinimumResponse.model_validate(tenant_request.unit).model_dump(mode="json")
                if tenant_request.unit
                else None
            )
    
    response.booking = booking_data
    return response


@router.post("/create_invoice", response_model=InvoiceResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    email_service = EmailService()
    if not isinstance(current_user, User):
        return current_user
    try:
        created_invoice = invoice_service.create(db, invoice)
        response = format_invoice_response(db, created_invoice)
        
        # Send email notification (fire and forget)
        if current_user.email:
            asyncio.create_task(email_service.send_create_action_email(
                current_user.email, "Invoice", created_invoice.id)
            )
            
        return data_response(response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/my_invoices", response_model=List[InvoiceResponse])
def read_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        # Get invoices where current user is either the tenant or the property owner
        invoices = invoice_service.get_for_user(
            db, current_user=current_user, skip=skip, limit=limit
        )
        
        # Format responses
        formatted_invoices = []
        for invoice in invoices:
            response = format_invoice_response(db, invoice)
            formatted_invoices.append(response.model_dump(mode="json"))
            
        return data_response(formatted_invoices)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
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
        
    booking = getattr(db_invoice, "booking", None)
    if booking is None:
        return not_found_error("Invoice has no associated booking")
        
    # Check authorization - allow access if user is either:
    # 1. The property owner of the related property, or
    # 2. The tenant associated with the booking
    property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
    is_property_owner = property_obj and property_obj.owner_id == current_user.id
    is_tenant = booking.tenant_id == current_user.id
    
    # Also check if user is tenant via tenant request
    is_tenant_via_request = False
    if booking.tenant_request_id:
        tenant_request = db.query(TenantRequest).filter(TenantRequest.id == booking.tenant_request_id).first()
        if tenant_request and tenant_request.tenant_id == current_user.id:
            is_tenant_via_request = True
    
    if not (is_property_owner or is_tenant or is_tenant_via_request):
        return forbidden_error("You do not have permission to view this invoice.")
    
    # Format response
    response = format_invoice_response(db, db_invoice)
    return data_response(response.model_dump(mode="json"))


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    email_service = EmailService()
    if not isinstance(current_user, User):
        return current_user
    try:
        invoice_to_check = invoice_service.get(db, invoice_id=invoice_id)
        if not invoice_to_check:
            return not_found_error(f"Invoice with ID {invoice_id} not found.")

        if not invoice_to_check.booking:
            return internal_server_error("Booking data associated with invoice is missing.")

        if not invoice_to_check.booking.property:
            return internal_server_error("Property data associated with booking is missing.")

        if invoice_to_check.booking.property.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this invoice.")

        db_invoice = invoice_service.update(db, invoice_id=invoice_id, invoice=invoice)
        if db_invoice is None:
            return not_found_error(f"Invoice with ID {invoice_id} update failed.")
            
        # Format response
        response = format_invoice_response(db, db_invoice)
                
        # Send email notification
        if current_user.email:
            await email_service.send_update_action_email(current_user.email, "Invoice", db_invoice.id)
            
        return data_response(response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    email_service = EmailService()
    if not isinstance(current_user, User):
        return current_user
        
    db_invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.booking))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    
    if db_invoice is None:
        return not_found_error("Invoice not found")
        
    booking = getattr(db_invoice, "booking", None)
    if booking is None:
        return not_found_error("Invoice has no associated booking")
        
    # Ensure only property owner can delete
    property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
    if not property_obj or property_obj.owner_id != current_user.id:
        return forbidden_error("Only the property owner can delete this invoice.")
        
    # Send email notification
    if current_user.email:
        await email_service.send_delete_action_email(current_user.email, "Invoice", invoice_id)
        
    deleted = invoice_service.delete(db, invoice_id)
    if not deleted:
        return not_found_error("Invoice not found")
        
    return empty_response()