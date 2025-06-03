from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import traceback

from schemas.booking_schema import (
    BookingCreate,
    BookingUpdate,
)
from schemas.booking_response import BookingResponse
from services.booking_service import BookingService
from services.property_service import PropertyService
from services.unit_service import UnitService
from database.models.user_model import User
from database.models.property_model import Property
from database.models.booking_model import Booking
from utils.dependencies import get_current_user, get_db
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
    bad_request_error,
)
from utils.id_generator import generate_unit_id

from services.tenant_request_service import TenantRequestService
from services.email_service import EmailService
from enums.booking_status import BookingStatus  


router = APIRouter(prefix="/bookings", tags=["Bookings"])
booking_service = BookingService()
tenant_request_service = TenantRequestService()
property_service = PropertyService()
unit_service = UnitService()
email_service = EmailService()


@router.get("/my-bookings", response_model=List[BookingResponse])
async def get_my_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns all tenant bookings for properties owned by the authenticated property owner.
    Only property owners can access this endpoint.
    """
    if not isinstance(current_user, User):
        return current_user

    if not booking_service.is_property_owner(db, current_user.id):
        return forbidden_error("Only property owners can access this endpoint.")

    try:
        owner_properties = (
            db.query(Property).filter(Property.owner_id == current_user.id).all()
        )
        owner_property_ids = [p.id for p in owner_properties]

        bookings = (
            db.query(Booking).filter(Booking.property_id.in_(owner_property_ids)).all()
        )

        formatted_bookings = []
        for booking in bookings:
            response = booking_service.format_booking_response(booking, db)
            if booking.unit_id:
                response["unit_id"] = generate_unit_id(booking.unit_id)
            if booking.tenant_request and booking.tenant_request.unit_id:
                response["tenant_request"]["unit_id"] = generate_unit_id(
                    booking.tenant_request.unit_id
                )
            formatted_bookings.append(response)
        return data_response(formatted_bookings)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/tenant-bookings/{tenant_id}", response_model=List[BookingResponse])
async def get_tenant_bookings(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns tenant bookings with different access levels:
    - Tenants can only see their own request-based bookings
    - Property owners can see all bookings for this tenant related to their properties
    """
    if not isinstance(current_user, User):
        return current_user

    try:
        if current_user.id == tenant_id:
            bookings = (
                db.query(Booking)
                .filter(
                    Booking.tenant_id == tenant_id, Booking.booked_by_owner == False
                )
                .all()
            )
            return data_response(
                [booking_service.format_booking_response(b, db) for b in bookings]
            )

        if booking_service.is_property_owner(db, current_user.id):
            owner_properties = (
                db.query(Property).filter(Property.owner_id == current_user.id).all()
            )
            owner_property_ids = [p.id for p in owner_properties]

            bookings = (
                db.query(Booking)
                .filter(
                    Booking.tenant_id == tenant_id,
                    Booking.property_id.in_(owner_property_ids),
                )
                .all()
            )
            bookings_response = []
            for b in bookings:
                response = booking_service.format_booking_response(b, db)
                if b.unit_id:
                    response["unit_id"] = generate_unit_id(b.unit_id)
                if b.tenant_request and b.tenant_request.unit_id:
                    response["tenant_request"]["unit_id"] = generate_unit_id(
                        b.tenant_request.unit_id
                    )
                bookings_response.append(response)
            return data_response(bookings_response)

        return forbidden_error("You are not authorized to view these bookings")

    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


# @router.get("/owner-bookings", response_model=List[BookingResponse])
# async def get_owner_bookings(
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """
#     Returns only bookings that the authenticated property owner created for their own tenants.
#     """
#     """Get owner's created bookings"""
#     if not isinstance(current_user, User):
#         return current_user

#     try:
#         # Verify owner access
#         if not booking_service.is_property_owner(db, current_user.id):
#             return forbidden_error("Only property owners can access this endpoint")

#         bookings = booking_service.get_owner_property_bookings(db, current_user.id)
#         return data_response([
#             booking_service.format_booking_response(b, db) for b in bookings
#         ])
#     except Exception as e:
#         traceback.print_exc()
#         return internal_server_error(str(e))


@router.get("/property/{property_id}", response_model=List[BookingResponse])
async def get_bookings_for_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns all bookings for a specific property (both owner-created and tenant-requested).
    Only accessible by the property owner.
    """
    if not isinstance(current_user, User):
        return current_user
    try:
        property_obj = (
            db.query(Property)
            .filter(Property.id == property_id, Property.owner_id == current_user.id)
            .first()
        )

        if not property_obj:
            return forbidden_error("You don't have access to this property's bookings")

        all_bookings = (
            db.query(Booking).filter(Booking.property_id == property_id).all()
        )

        if not all_bookings:
            return data_response([])

        formatted_bookings = [
            booking_service.format_booking_response(booking, db, property_obj)
            for booking in all_bookings
        ]

        return data_response(formatted_bookings)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns details of a specific booking:
    - Property owners can view any booking for their properties
    - Tenants can only view their own request-based bookings
    """
    if not isinstance(current_user, User):
        return current_user

    try:
        booking = booking_service.get(db, booking_id)
        if not booking:
            return not_found_error(f"Booking {booking_id} not found")

        property_obj = (
            db.query(Property)
            .filter(
                Property.id == booking.property_id, Property.owner_id == current_user.id
            )
            .first()
        )

        response = booking_service.format_booking_response(booking, db)
        if booking.unit_id:
            response["unit_id"] = generate_unit_id(booking.unit_id)
        if booking.tenant_request and booking.tenant_request.unit_id:
            response["tenant_request"]["unit_id"] = generate_unit_id(
                booking.tenant_request.unit_id
            )

        if property_obj:
            return data_response(response)

        if booking.tenant_id == current_user.id and not booking.booked_by_owner:
            return data_response(response)

        return forbidden_error("Not authorized to view this booking")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Updates booking status. Owners can update any status, tenants can only cancel their own bookings."""
    if not isinstance(current_user, User):
        return current_user
    try:
        existing_booking = booking_service.get_booking(db, booking_id)
        if not existing_booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        property = db.query(Property).filter(Property.id == existing_booking.property_id).first()
        is_owner = property and property.owner_id == current_user.id

        try:
            status = BookingStatus(booking_in.status)
        except ValueError:
            return bad_request_error(f"Invalid status: {booking_in.status}")

        updated_booking = await booking_service.update_status(
            db=db,
            booking_id=booking_id,
            new_status=status,
            user_id=current_user.id,
            is_owner=is_owner,
        )

        if not updated_booking:
            return not_found_error("Invalid status transition")

        response = booking_service.format_booking_response(updated_booking, db, property)
        return data_response(response)

    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Deletes a booking. Owners can delete any booking, tenants can only delete their pending bookings.
    """
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = booking_service.get(db, booking_id)
        if not booking:
            return not_found_error(f"Booking {booking_id} not found")

        result = booking_service.delete_booking(db, booking_id, current_user.id)
        if not result:
            return not_found_error(
                f"Booking with ID {booking_id} not found or you are not authorized to delete it."
            )

        # Send email to tenant about booking deletion
        if booking.tenant and booking.tenant.email:
            await email_service.send_delete_action_email(
                booking.tenant.email,
                "Booking",
                booking_id
            )

        return empty_response()
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.post("/create-booking", response_model=BookingResponse)
async def create_bookings(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Creates a new booking. Only property owners can create bookings directly for their properties and tenants.
    """
    if not isinstance(current_user, User):
        return current_user
    try:
        # Check if user is the property owner
        property_obj = (
            db.query(Property).filter(Property.id == booking_in.property_id).first()
        )
        is_owner = property_obj and property_obj.owner_id == current_user.id

        # Validate property owner permissions
        if not is_owner and not booking_service.is_property_owner(db, current_user.id):
            return forbidden_error("Only property owners can create bookings directly.")

        if not booking_in.tenant_id:
            return bad_request_error(
                "A valid User ID must be provided when creating a booking."
            )

        # Validate unit and floor if provided
        if booking_in.unit_id and booking_in.floor_id:
            if not booking_service.validate_unit_and_floor(
                db, booking_in.unit_id, booking_in.floor_id, booking_in.property_id
            ):
                return conflict_error("Invalid unit or floor configuration")

        created_booking = booking_service.create(
            db,
            booking_in,
            actual_tenant_id=booking_in.tenant_id,
            tenant_request_id=None,
            booked_by_owner=is_owner,
        )

        if not created_booking:
            return conflict_error(
                "Could not create booking. Property/Unit might be unavailable."
            )

        if current_user.email:
            await email_service.send_create_action_email(
                current_user.email, "Booking", created_booking.id
            )

        return data_response(
            booking_service.format_booking_response(created_booking, db, property_obj)
        )

    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

