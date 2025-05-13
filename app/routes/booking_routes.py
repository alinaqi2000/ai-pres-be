from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import traceback

from schemas.booking_schema import (
    BookingCreate,
    BookingUpdate,
    BookingStatusUpdate,
)
from schemas.booking_response import BookingResponse
from services.booking_service import BookingService
from database.models.user_model import User
from database.models.property_model import Property, Unit, Floor
from database.models.tenant_model import Tenant # Added Tenant import
from database.models.booking_model import Booking
from database.models import Floor
from database.models import Unit
from database.models.tenant_request_model import TenantRequest
from enums.booking_status import BookingStatus
from utils.dependencies import get_current_user, get_db
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
    bad_request_error
)
from enums.booking_status import BookingStatus

from services.tenant_request_service import TenantRequestService
from database.models.tenant_request_model import TenantRequest


router = APIRouter(prefix="/bookings", tags=["Bookings"])
booking_service = BookingService()
tenant_request_service = TenantRequestService()

@router.post("/create_booking", response_model=BookingResponse)
def create_bookings(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        property_obj = None
        if booking_in.property_id and not booking_in.unit_id and not booking_in.floor_id:
            property_obj = (
                db.query(Property).filter(Property.id == booking_in.property_id).first()
            )
            if not property_obj:
                return not_found_error(
                    f"Property with ID {booking_in.property_id} not found."
                )
            if property_obj.owner_id != current_user.id:
                return forbidden_error(
                    "You are not authorized to create a booking for this property."
                )
            if not booking_in.tenant_id:
                return bad_request_error("A valid Tenant ID must be provided when an owner creates a booking.")
            
            tenant_record = db.query(Tenant).filter(Tenant.id == booking_in.tenant_id).first()
            if not tenant_record:
                return not_found_error(f"Tenant with ID {booking_in.tenant_id} not found.")
            
            if tenant_record.owner_id != current_user.id:
                return forbidden_error(f"You can only create bookings for tenants linked to your account. Tenant ID {booking_in.tenant_id} is not associated with you.")
            
            actual_tenant_id_for_booking = tenant_record.id

            property_booking = booking_service.create(
                db,
                booking_in,
                actual_tenant_id=actual_tenant_id_for_booking,
                tenant_request_id=None,
                booked_by_owner=True
            )

            if property_booking:
                return data_response(BookingResponse.model_validate(property_booking).model_dump(mode="json"))
            else:
                return conflict_error(
                    f"Could not book property {booking_in.property_id}. One or more units may be unavailable or already booked by you for this tenant for an overlapping period."
                )

        elif booking_in.property_id and booking_in.unit_id and booking_in.floor_id:
            property_obj = (
                db.query(Property).filter(Property.id == booking_in.property_id).first()
            )
            if not property_obj:
                return not_found_error(
                    f"Property with ID {booking_in.property_id} not found."
                )
            if property_obj.owner_id != current_user.id:
                return forbidden_error(
                    "You are not authorized to create a booking for this property."
                )
            if not booking_in.tenant_id:
                return bad_request_error("A valid Tenant ID must be provided when an owner creates a booking.")
            
            tenant_record = db.query(Tenant).filter(Tenant.id == booking_in.tenant_id).first()
            if not tenant_record:
                return not_found_error(f"Tenant with ID {booking_in.tenant_id} not found.")
            
            if tenant_record.owner_id != current_user.id:
                return forbidden_error(f"You can only create bookings for tenants linked to your account. Tenant ID {booking_in.tenant_id} is not associated with you.")
            
            actual_tenant_id_for_booking = tenant_record.id 
            unit_check = db.query(Unit).filter(Unit.id == booking_in.unit_id, Unit.property_id == property_obj.id).first()
            floor_check = db.query(Floor).filter(Floor.id == booking_in.floor_id, Floor.property_id == property_obj.id).first()
            if not unit_check or not floor_check or unit_check.floor_id != floor_check.id:
                return conflict_error("Unit or Floor ID is invalid or does not belong to the specified property.")

            single_booking = booking_service.create(
                db,
                booking_in,
                actual_tenant_id=actual_tenant_id_for_booking,
                tenant_request_id=None,
                booked_by_owner=True
            )
            if single_booking:
                return data_response(BookingResponse.model_validate(single_booking).model_dump(mode="json"))
            else:
                return conflict_error("Could not create booking. Unit/Property might be unavailable or request invalid.")

        elif booking_in.unit_id: 
            unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
            if not unit:
                return not_found_error(f"Unit with ID {booking_in.unit_id} not found.")

            floor = db.query(Floor).filter(Floor.id == unit.floor_id).first()
            if not floor:
                return not_found_error(
                    f"Floor for unit {booking_in.unit_id} not found."
                )

            property_obj = (
                db.query(Property).filter(Property.id == floor.property_id).first()
            )
            if not property_obj:
                return not_found_error(f"Property for floor {floor.id} not found.")

            booking_in.property_id = property_obj.id
            booking_in.floor_id = floor.id

            tenant_request = None
            if booking_in.tenant_request_id:
                tenant_request = tenant_request_service.get_tenant_request_by_id(db, booking_in.tenant_request_id)
                if not tenant_request:
                    return not_found_error(
                        f"Tenant request with ID {booking_in.tenant_request_id} not found."
                    )
                if tenant_request.tenant_id != current_user.id:
                    return forbidden_error(
                        "Not authorized: Tenant request does not belong to you."
                    )
                if tenant_request.unit_id != booking_in.unit_id:
                     return conflict_error(
                        "Tenant request unit ID does not match the booking unit ID."
                    )
                if tenant_request.status != "accepted":
                    return conflict_error(
                        f"Tenant request {booking_in.tenant_request_id} has not been accepted. Current status: {tenant_request.status}"
                    )
            else:
                tenant_request = (
                    db.query(TenantRequest)
                    .filter(
                        TenantRequest.tenant_id == current_user.id,
                        TenantRequest.unit_id == booking_in.unit_id,
                        TenantRequest.status == "accepted",
                    )
                    .order_by(TenantRequest.created_at.desc())
                    .first()
                )
                if not tenant_request:
                    return conflict_error(
                        "No accepted tenant request found for this unit. Please create a tenant request or specify an accepted tenant_request_id."
                    )
            
            if property_obj.owner_id == current_user.id:
                return forbidden_error(
                    "Owners cannot create bookings via the tenant flow for their own properties. Please use the owner booking flow (provide property_id, no unit_id/floor_id)."
                )
            created_booking = booking_service.create(
                db, 
                booking_in, 
                actual_tenant_id=None, 
                tenant_request_id=tenant_request.id,
                booked_by_owner=False
            )
            if not created_booking:
                return conflict_error(
                    "Could not create booking. Unit might be unavailable for new dates or request invalid."
                )
            return data_response(
                BookingResponse.model_validate(created_booking).model_dump(mode="json")
            )
        
        else:
            return conflict_error(
                "Invalid booking request: Either provide 'property_id' (for owner booking entire property) OR 'unit_id' (for tenant booking a floor)."
            )

    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/properties/{property_id}/bookings/", response_model=List[BookingResponse])
def get_bookings_for_property(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        return not_found_error(f"Property with ID {property_id} not found.")

    if property_obj.owner_id != current_user.id:
        return forbidden_error(
            "You are not authorized to view bookings for this property."
        )

    try:
        bookings = booking_service.get_by_property(
            db, property_id=property_id, skip=skip, limit=limit
        )
        return data_response(
            [
                BookingResponse.model_validate(b).model_dump(mode="json")
                for b in bookings
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/my_bookings", response_model=List[BookingResponse])
def get_my_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        bookings = booking_service.get_by_tenant(db, current_user.id, skip, limit)
        return data_response(
            [
                BookingResponse.model_validate(b).model_dump(mode="json")
                for b in bookings
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/property_owner", response_model=List[BookingResponse])
def get_bookings_for_my_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        bookings = booking_service.get_by_property_owner(
            db, current_user.id, skip, limit
        )
        return data_response(
            [
                BookingResponse.model_validate(b).model_dump(mode="json")
                for b in bookings
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = booking_service.get(db, booking_id)
        if not booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == booking.property_id).first()
        # Check if the current user is the tenant via TenantRequest
        is_tenant_via_request = False
        if booking.tenant_request_id:
            tenant_request = db.query(TenantRequest).filter(TenantRequest.id == booking.tenant_request_id).first()
            if tenant_request and tenant_request.tenant_id == current_user.id:
                is_tenant_via_request = True

        if not (
            (booking.tenant_id == current_user.id and booking.tenant_id is not None) # Explicit tenant_id link (e.g. owner booked for tenant)
            or is_tenant_via_request  # Tenant booked for themselves via TenantRequest
            or (prop and prop.owner_id == current_user.id) # User is the property owner
        ):
            return forbidden_error("Not authorized to view this booking.")

        return data_response(
            BookingResponse.model_validate(booking).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        db_booking = booking_service.get(db, booking_id)
        if not db_booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        can_update = False
        prop = db.query(Property).filter(Property.id == db_booking.property_id).first()
        is_owner = prop and prop.owner_id == current_user.id

        is_tenant_via_request = False
        if db_booking.tenant_request_id:
            tenant_request = db.query(TenantRequest).filter(TenantRequest.id == db_booking.tenant_request_id).first()
            if tenant_request and tenant_request.tenant_id == current_user.id:
                is_tenant_via_request = True

        # Scenario 1: Current user is the tenant who made the booking (via direct tenant_id or via TenantRequest)
        # and the booking is PENDING.
        is_direct_tenant = db_booking.tenant_id == current_user.id and db_booking.tenant_id is not None

        if (
            (is_direct_tenant or is_tenant_via_request)
            and db_booking.status == BookingStatus.PENDING
        ):
            allowed_tenant_updates = ["start_date", "end_date", "notes"]
            for field in booking_in.model_dump(exclude_unset=True).keys():
                if field not in allowed_tenant_updates:
                    return forbidden_error(f"Tenants cannot update '{field}'.")
            can_update = True
        elif is_owner:
            if booking_in.status and booking_in.status != db_booking.status:
                return forbidden_error(
                    "Please use the dedicated status update endpoint for changing booking status."
                )
            can_update = True

        if not can_update:
            return forbidden_error(
                "Not authorized to update this booking or perform this specific update."
            )

        updated_booking = booking_service.update(db, db_booking, booking_in)
        if not updated_booking:
            return conflict_error(
                "Could not update booking. Unit might be unavailable for new dates or update invalid."
            )
        return data_response(
            BookingResponse.model_validate(updated_booking).model_dump(mode="json")
        )
    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        db_booking = booking_service.get(db, booking_id)
        if not db_booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == db_booking.property_id).first()
        is_owner = prop and prop.owner_id == current_user.id

        updated_booking = booking_service.update_status(
            db, booking_id, status_update.status, current_user.id, is_owner
        )
        if not updated_booking:
            return forbidden_error(
                "Not authorized to change status or invalid status transition."
            )
        return data_response(
            BookingResponse.model_validate(updated_booking).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        db_booking = booking_service.get(db, booking_id)
        if not db_booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == db_booking.property_id).first()
        is_owner = prop and prop.owner_id == current_user.id

        success = booking_service.delete(db, booking_id, current_user.id, is_owner)
        if not success:
            return forbidden_error(
                "Not authorized to delete this booking or deletion not allowed at current stage."
            )
        return empty_response()
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
