from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import traceback

from schemas.booking_schema import (
    BookingCreate,
    BookingUpdate,
    BookingOut,
    BookingStatusUpdate,
)
from services.booking_service import BookingService
from database.models.user_model import User
from database.models.property_model import Property
from database.models import Floor
from database.models import Unit
from utils.dependencies import get_current_user, get_db
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
)
from enums.booking_status import BookingStatus

router = APIRouter(prefix="/bookings", tags=["Bookings"])
booking_service = BookingService()


@router.post("/create_booking", response_model=BookingOut)
def create_bookings(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        property = (
            db.query(Property).filter(Property.id == booking_in.property_id).first()
        )
        if not property:
            return not_found_error(
                f"Property with ID {booking_in.property_id} not found."
            )
        floor = db.query(Floor).filter(Floor.id == booking_in.floor_id).first()
        if not floor:
            return not_found_error(f"Floor with ID {booking_in.floor_id} not found.")
        unit = db.query(Unit).filter(Unit.id == booking_in.unit_id).first()
        if not unit:
            return not_found_error(f"Unit with ID {booking_in.unit_id} not found.")

        created_booking = booking_service.create(db, booking_in, current_user.id)
        if not created_booking:
            return conflict_error(
                "Could not create booking. Unit might be unavailable or request invalid."
            )
        return data_response(
            BookingOut.model_validate(created_booking).model_dump(mode="json")
        )
    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/my_bookings", response_model=List[BookingOut])
def get_my_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        bookings = booking_service.get_by_tenant(db, current_user.id, skip, limit)
        return data_response(
            [BookingOut.model_validate(b).model_dump(mode="json") for b in bookings]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/property_owner", response_model=List[BookingOut])
def get_bookings_for_my_properties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        bookings = booking_service.get_by_property_owner(
            db, current_user.id, skip, limit
        )
        return data_response(
            [BookingOut.model_validate(b).model_dump(mode="json") for b in bookings]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = booking_service.get(db, booking_id)
        if not booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == booking.property_id).first()
        if not (
            booking.tenant_id == current_user.id
            or (prop and prop.owner_id == current_user.id)
        ):
            return forbidden_error("Not authorized to view this booking.")

        return data_response(BookingOut.model_validate(booking).model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: int,
    booking_in: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

        if (
            db_booking.tenant_id == current_user.id
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
            BookingOut.model_validate(updated_booking).model_dump(mode="json")
        )
    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
            BookingOut.model_validate(updated_booking).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        db_booking = booking_service.get(
            db, booking_id
        )  # Get booking to check ownership/status
        if not db_booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == db_booking.property_id).first()
        is_owner = prop and prop.owner_id == current_user.id

        success = booking_service.delete(db, booking_id, current_user.id, is_owner)
        if not success:
            # This could be due to not found (already handled) or permission issues based on service logic
            return forbidden_error(
                "Not authorized to delete this booking or deletion not allowed at current stage."
            )
        return empty_response()
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
