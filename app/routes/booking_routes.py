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
from database.models.booking_model import Booking
from database.models.property_model import Property, Unit, Floor
from database.models import Floor
from database.models import Unit
from database.models.tenant_request_model import TenantRequest
from enums.booking_status import BookingStatus
from utils.dependencies import get_current_user, get_db
from utils import generate_property_id
from schemas.auth_schema import UserMinimumResponse
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
    bad_request_error,
)
from enums.booking_status import BookingStatus

from services.tenant_request_service import TenantRequestService
from services.email_service import EmailService
from database.models.tenant_request_model import TenantRequest


router = APIRouter(prefix="/bookings", tags=["Bookings"])
booking_service = BookingService()
tenant_request_service = TenantRequestService()
email_service = EmailService()


def set_booking_response_data(
    response: BookingResponse,
    booking: Booking,
    db: Session,
    property_obj: Property = None,
):
    """Helper function to set property_id and owner data on booking responses"""
    if (
        hasattr(response, "property")
        and response.property
        and not response.property.property_id
    ):
        response.property.property_id = generate_property_id(response.property.id)

    if (
        response.tenant_request
        and hasattr(response.tenant_request, "property")
        and response.tenant_request.property
        and not response.tenant_request.property.property_id
    ):
        response.tenant_request.property.property_id = generate_property_id(
            response.tenant_request.property.id
        )

    # Set owner information
    if not property_obj:
        property_obj = (
            db.query(Property).filter(Property.id == booking.property_id).first()
        )

    if property_obj:
        owner_obj = db.query(User).filter(User.id == property_obj.owner_id).first()
        if owner_obj:
            response.owner = UserMinimumResponse.model_validate(owner_obj)

    return response


@router.get("/properties/{property_id}/bookings/", response_model=List[BookingResponse])
async def get_bookings_for_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            return not_found_error(f"Property with ID {property_id} not found.")
        if property_obj.owner_id != current_user.id:
            return forbidden_error(
                "Only the property owner can view bookings for their property."
            )

        all_bookings = []
        tenant_bookings = booking_service.get_bookings_for_property(db, property_id)
        all_bookings.extend(tenant_bookings)

        formatted_bookings = []
        for booking in all_bookings:
            response = BookingResponse.model_validate(booking)
            response = set_booking_response_data(response, booking, db, property_obj)
            formatted_bookings.append(response.model_dump(mode="json"))

        return data_response(formatted_bookings)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/my_bookings", response_model=List[BookingResponse])
async def get_my_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    is_property_owner = (
        db.query(Property).filter(Property.owner_id == current_user.id).first()
        is not None
    )
    if not is_property_owner:
        return forbidden_error("Only property owners can access this endpoint.")
    try:
        owned_properties = (
            db.query(Property).filter(Property.owner_id == current_user.id).all()
        )
        property_ids = [p.id for p in owned_properties]
        bookings = db.query(Booking).filter(Booking.property_id.in_(property_ids)).all()

        formatted_bookings = []
        for booking in bookings:
            response = BookingResponse.model_validate(booking)
            response = set_booking_response_data(response, booking, db)
            formatted_bookings.append(response.model_dump(mode="json"))

        return data_response(formatted_bookings)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/property_owner", response_model=List[BookingResponse])
async def get_property_owner_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        bookings = booking_service.get_property_owner_bookings(db, current_user.id)
        formatted_bookings = []
        for booking in bookings:
            response = BookingResponse.model_validate(booking)
            response = set_booking_response_data(response, booking, db)
            formatted_bookings.append(response.model_dump(mode="json"))

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
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = booking_service.get_booking(db, booking_id)
        if not booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")

        prop = db.query(Property).filter(Property.id == booking.property_id).first()
        is_owner = prop and prop.owner_id == current_user.id

        is_tenant_via_request = False
        if booking.tenant_request_id:
            tenant_request = (
                db.query(TenantRequest)
                .filter(TenantRequest.id == booking.tenant_request_id)
                .first()
            )
            if tenant_request and tenant_request.tenant_id == current_user.id:
                is_tenant_via_request = True

        if not (
            (booking.tenant_id == current_user.id) or is_tenant_via_request or is_owner
        ):
            return forbidden_error("You are not authorized to view this booking.")

        response = BookingResponse.model_validate(booking)
        response = set_booking_response_data(response, booking, db, prop)

        return data_response(response.model_dump(mode="json"))
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
    if not isinstance(current_user, User):
        return current_user
    try:
        booking = booking_service.update_booking(
            db, booking_id, booking_in, current_user.id
        )
        if not booking:
            return not_found_error(f"Booking with ID {booking_id} not found.")
        return data_response(
            BookingResponse.model_validate(booking).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        result = booking_service.delete_booking(db, booking_id, current_user.id)
        if not result:
            return not_found_error(
                f"Booking with ID {booking_id} not found or you are not authorized to delete it."
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
    if not isinstance(current_user, User):
        return current_user
    try:
        property_obj = None
        if (
            booking_in.property_id
            and not booking_in.unit_id
            and not booking_in.floor_id
        ):
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
                return bad_request_error(
                    "A valid User ID must be provided when an owner creates a booking."
                )

            tenant_user = db.query(User).filter(User.id == booking_in.tenant_id).first()
            if not tenant_user:
                return not_found_error(
                    f"User with ID {booking_in.tenant_id} not found."
                )

            if (
                not tenant_user.booked_by_owner
                or tenant_user.created_by_owner_id != current_user.id
            ):
                return forbidden_error(
                    f"You can only create bookings for users that were created by you. User ID {booking_in.tenant_id} is not associated with you."
                )

            actual_tenant_id_for_booking = tenant_user.id

            existing_booking = (
                db.query(Booking)
                .filter(
                    Booking.tenant_id == actual_tenant_id_for_booking,
                    Booking.property_id == booking_in.property_id,
                )
                .first()
            )
            if existing_booking:
                return conflict_error("Tenant already has a booking for this property.")

            property_booking = booking_service.create(
                db,
                booking_in,
                actual_tenant_id=actual_tenant_id_for_booking,
                tenant_request_id=None,
                booked_by_owner=True,
            )

            if property_booking:
                if current_user.email:
                    await email_service.send_create_action_email(
                        current_user.email, "Booking", property_booking.id
                    )
                response = BookingResponse.model_validate(property_booking)

                if (
                    hasattr(response, "property")
                    and response.property
                    and not response.property.property_id
                ):
                    response.property.property_id = generate_property_id(
                        response.property.id
                    )

                if (
                    response.tenant_request
                    and hasattr(response.tenant_request, "property")
                    and response.tenant_request.property
                    and not response.tenant_request.property.property_id
                ):
                    response.tenant_request.property.property_id = generate_property_id(
                        response.tenant_request.property.id
                    )

                if property_obj:
                    owner_obj = (
                        db.query(User).filter(User.id == property_obj.owner_id).first()
                    )
                    if owner_obj:
                        response.owner = UserMinimumResponse.model_validate(owner_obj)

                return data_response(response.model_dump(mode="json"))
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
                return bad_request_error(
                    "A valid Tenant ID must be provided when an owner creates a booking."
                )

            tenant_user = db.query(User).filter(User.id == booking_in.tenant_id).first()
            if not tenant_user:
                return not_found_error(
                    f"User with ID {booking_in.tenant_id} not found."
                )

            if not tenant_user.booked_by_owner:
                return forbidden_error(
                    f"You can only create bookings for users that were created by property owners. User ID {booking_in.tenant_id} is not associated with you."
                )

            actual_tenant_id_for_booking = tenant_user.id
            unit_check = (
                db.query(Unit)
                .filter(
                    Unit.id == booking_in.unit_id, Unit.property_id == property_obj.id
                )
                .first()
            )
            floor_check = (
                db.query(Floor)
                .filter(
                    Floor.id == booking_in.floor_id,
                    Floor.property_id == property_obj.id,
                )
                .first()
            )
            if (
                not unit_check
                or not floor_check
                or unit_check.floor_id != floor_check.id
            ):
                return conflict_error(
                    "Unit or Floor ID is invalid or does not belong to the specified property."
                )

            single_booking = booking_service.create(
                db,
                booking_in,
                actual_tenant_id=actual_tenant_id_for_booking,
                tenant_request_id=None,
                booked_by_owner=True,
            )
            if single_booking:
                if current_user.email:
                    await email_service.send_create_action_email(
                        current_user.email, "Booking", single_booking.id
                    )
                response = BookingResponse.model_validate(single_booking)

                if (
                    hasattr(response, "property")
                    and response.property
                    and not response.property.property_id
                ):
                    response.property.property_id = generate_property_id(
                        response.property.id
                    )

                if (
                    response.tenant_request
                    and hasattr(response.tenant_request, "property")
                    and response.tenant_request.property
                    and not response.tenant_request.property.property_id
                ):
                    response.tenant_request.property.property_id = generate_property_id(
                        response.tenant_request.property.id
                    )

                if property_obj:
                    owner_obj = (
                        db.query(User).filter(User.id == property_obj.owner_id).first()
                    )
                    if owner_obj:
                        response.owner = UserMinimumResponse.model_validate(owner_obj)

                return data_response(response.model_dump(mode="json"))
            else:
                return conflict_error(
                    "Could not create booking. Unit/Property might be unavailable or request invalid."
                )

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
                tenant_request = tenant_request_service.get_tenant_request_by_id(
                    db, booking_in.tenant_request_id
                )
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
                booked_by_owner=False,
            )
            if not created_booking:
                return conflict_error(
                    "Could not create booking. Unit might be unavailable for new dates or request invalid."
                )
            response = BookingResponse.model_validate(created_booking)

            if (
                hasattr(response, "property")
                and response.property
                and not response.property.property_id
            ):
                response.property.property_id = generate_property_id(
                    response.property.id
                )

            if (
                response.tenant_request
                and hasattr(response.tenant_request, "property")
                and response.tenant_request.property
                and not response.tenant_request.property.property_id
            ):
                response.tenant_request.property.property_id = generate_property_id(
                    response.tenant_request.property.id
                )

            if property_obj:
                owner_obj = (
                    db.query(User).filter(User.id == property_obj.owner_id).first()
                )
                if owner_obj:
                    response.owner = UserMinimumResponse.model_validate(owner_obj)

            return data_response(response.model_dump(mode="json"))

        else:
            return conflict_error(
                "Invalid booking request: Either provide 'property_id' (for owner booking entire property) OR 'unit_id' (for tenant booking a floor)."
            )

    except ValueError as ve:
        return conflict_error(str(ve))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
