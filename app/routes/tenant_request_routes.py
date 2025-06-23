from schemas.booking_schema import BookingUpdate
from database.models.tenant_request_model import TenantRequest
from enums.booking_status import BookingStatus
from enums.tenant_request_status import TenantRequestStatus
from enums.tenant_request_type import TenantRequestType
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from typing import List

from database.models.property_model import Property, Floor, Unit
from database.models.user_model import User
from schemas.tenant_request_schema import (
    TenantRequestCreate,
    TenantRequestUpdate,
)
from schemas.tenant_request_response import TenantRequestResponse
from services.tenant_request_service import TenantRequestService
from services.booking_service import BookingService
from utils.dependencies import get_current_user, get_db
from utils import generate_property_id
from utils.id_generator import generate_unit_id
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
)
from services.email_service import EmailService
import traceback
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


router = APIRouter(prefix="/tenant_requests", tags=["Tenant Requests"])
tenant_request_service = TenantRequestService()
booking_service = BookingService()
email_service = EmailService()


@router.post("/create_request", response_model=TenantRequestResponse)
async def create_request(
    request: TenantRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        request_id = None
        if request.type == TenantRequestType.BOOKING.value:
            if booking_service.is_property_occupied(db, request.property_id, request.start_date):
                return conflict_error(
                    "This property is currently booked and not available for tenant requests."
                )

            start_date = request.start_date.replace(tzinfo=timezone.utc)
        
            if request.end_date is not None:
                end_date = request.end_date.replace(tzinfo=timezone.utc)
                
                min_end_date = start_date + relativedelta(months=1, days=-1)
                
                if end_date < min_end_date:
                    return conflict_error(
                        "Booking duration must be at least one full calendar month. "
                        f"Minimum end date would be {min_end_date.date()}"
                    )
                

            existing = tenant_request_service.check_existing_request(
                db, current_user.id, request
            )
            if existing:
                return conflict_error(
                    "Tenant has already made a request for this property."
                )

            if not request.unit_id:
                return conflict_error("unit_id is required to make a tenant request.")

            unit_obj = (
                db.query(Unit)
                .options(selectinload(Unit.floor).selectinload(Floor.property))
                .filter(Unit.id == request.unit_id)
                .first()
            )

            if not unit_obj:
                return not_found_error(f"Unit with ID {request.unit_id} not found.")

            if unit_obj.is_occupied:
                return conflict_error(
                    f"Unit with ID {request.unit_id} is currently occupied and not available for requests."
                )

            floor_obj = unit_obj.floor
            property_obj = floor_obj.property
            request_id = property_obj.id
            if not floor_obj:
                return internal_server_error(
                    f"Critical: Floor not found for unit {unit_obj.id}. Data inconsistency."
                )
            if not property_obj:
                return internal_server_error(
                    f"Critical: Property not found for floor {floor_obj.id}. Data inconsistency."
                )

            if property_obj.owner_id == current_user.id:
                return forbidden_error(
                    "Property owners cannot make tenant requests for their own properties."
                )

            actual_request_payload = TenantRequestCreate(
                unit_id=unit_obj.id,
                floor_id=floor_obj.id,
                property_id=property_obj.id,
                tenant_id=current_user.id,
                owner_id=property_obj.owner_id,
                message=request.message,
                start_date=request.start_date,
                end_date=request.end_date,
                monthly_offer=request.monthly_offer,
                preferred_move_in=request.preferred_move_in,
            )
        else:
            booking = booking_service.get(db, request.booking_id)
            if not booking:
                return not_found_error(f"Booking with ID {request.booking_id} not found.")
            request_id = booking.id
            actual_request_payload = TenantRequestCreate(
                booking_id=booking.id,
                tenant_id=current_user.id,
                owner_id=booking.property.owner_id,
                message=request.message,
                type=request.type,
            )
        if actual_request_payload.type == TenantRequestType.BOOKING.value:
            existing_request = tenant_request_service.check_existing_request(
                db, current_user.id, actual_request_payload
            )
            if existing_request:
                return conflict_error(
                    "You have already made a request for this unit, or another pending/accepted request for you exists for this unit."
                )

        created_tenant_request = tenant_request_service.create(
            db,
            actual_request_payload,
        )

        await email_service.send_create_action_email(
            current_user.email, "Tenant Request", request_id
        )

        response = TenantRequestResponse.model_validate(created_tenant_request)
        if response.property and not response.property.property_id:
            response.property.property_id = generate_property_id(response.property.id)
        if response.unit:
            response.unit.unit_id = generate_unit_id(response.unit.id)
        return data_response(response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"An unexpected error occurred: {str(e)}")


@router.get("/cancellation", response_model=List[TenantRequestResponse])
async def list_all_cancellation_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        requests = tenant_request_service.get_all_cancellation_requests(db, current_user.id, skip, limit)
        responses = []
        for r in requests:
            response = TenantRequestResponse.model_validate(r)
            if response.property and not response.property.property_id:
                response.property.property_id = generate_property_id(response.property.id)
            if response.unit:
                response.unit.unit_id = generate_unit_id(response.unit.id)
            responses.append(response.model_dump(mode="json"))
        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

@router.patch("/update-request/{request_id}", response_model=TenantRequestResponse)
async def update_request_response(
    request_id: int,
    request_in: TenantRequestUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Updates tenant request status. Owners can update any status, tenants can only cancel their own bookings."""
    if not isinstance(current_user, User):
        return current_user
    try:
        request_to_check = tenant_request_service.get(db, request_id)
        if not request_to_check:
            return not_found_error(f"Tenant request with ID {request_id} not found.")

        if request_to_check.owner_id != current_user.id:
            return forbidden_error("Not authorized to update this request.")


        property = db.query(Property).filter(Property.id == request_to_check.property_id).first()
        is_owner = property and property.owner_id == current_user.id

        try:
            status = TenantRequestStatus(request_in.status)
        except ValueError:
            return bad_request_error(f"Invalid status: {request_in.status}")

        updated_request = tenant_request_service.update(
            db=db,
            request_id=request_id,
            request_in=request_in, 
            new_status=status,
            is_owner=is_owner,
            current_user=current_user,
        )
        if isinstance(updated_request, str):
            return internal_server_error(updated_request)

        if status == TenantRequestStatus.ACCEPTED:
            await booking_service.update(
                db=db,
                booking_id=request_to_check.booking_id,
                booking_in=BookingUpdate(
                    status=BookingStatus.CLOSED,
                    end_date=datetime.now(timezone.utc),
                ),
                is_owner=is_owner,
            )

        response = tenant_request_service.format_tenant_request_response(updated_request, db)
        return data_response(response)

    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/booking", response_model=List[TenantRequestResponse])
async def list_all_booking_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        requests = tenant_request_service.get_all_booking_requests(db, current_user.id, skip, limit)
        responses = []
        for r in requests:
            response = TenantRequestResponse.model_validate(r)
            if response.property and not response.property.property_id:
                response.property.property_id = generate_property_id(response.property.id)
            if response.unit:
                response.unit.unit_id = generate_unit_id(response.unit.id)
            responses.append(response.model_dump(mode="json"))
        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{request_id}", response_model=TenantRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        request = tenant_request_service.get(db, request_id)
        if not request:
            return not_found_error(f"Tenant request with ID {request_id} not found")
        response = TenantRequestResponse.model_validate(request)
        if response.property and not response.property.property_id:
            response.property.property_id = generate_property_id(response.property.id)
        if response.unit:
            response.unit.unit_id = generate_unit_id(response.unit.id)
        return data_response(response.model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{request_id}", response_model=TenantRequestUpdate)
async def update_request(
    request_id: int,
    update_data: TenantRequestUpdate, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        db_obj = tenant_request_service.get(db, request_id)
        if not db_obj:
            return not_found_error(f"Tenant request with ID {request_id} not found")

        if current_user.id == db_obj.property.owner_id:
            response_data = TenantRequestUpdate(
                status=update_data.status if update_data.status else db_obj.status,
                is_seen=update_data.is_seen if update_data.is_seen is not None else db_obj.is_seen
            )

            updated = False
            if update_data.status:
                updated = await tenant_request_service.update_status(
                    db=db,
                    request_id=request_id,
                    new_status=update_data.status,
                    user_id=current_user.id
                )

            if update_data.is_seen is not None:
                db_obj.is_seen = update_data.is_seen
                db.commit()
                db.refresh(db_obj)
                updated = True
                if not update_data.status:
                    await email_service.send_update_action_email(
                        current_user.email,
                        "Tenant Request Seen",
                        db_obj.unit_id
                    )

            if updated:
                return data_response(response_data.model_dump(mode="json"))
            
            return not_found_error("No updates were made")
        else:
            return forbidden_error("Not authorized to update this request")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{request_id}")
async def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        success = tenant_request_service.delete(db, request_id)
        if not success:
            return not_found_error(f"Tenant request with ID {request_id} not found")
        await email_service.send_delete_action_email(
            current_user.email, "Tenant Request", request_id
        )
        return empty_response()
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/property/{property_id}", response_model=List[TenantRequestResponse])
async def get_requests_by_property(
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=(Depends(get_current_user)),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            return not_found_error(f"Property with id {property_id} does not exist.")

        requests = tenant_request_service.get_by_property(db, property_id, skip, limit)
        responses = []
        for r in requests:
            response = TenantRequestResponse.model_validate(r)
            if response.property and not response.property.property_id:
                response.property.property_id = generate_property_id(response.property.id)
            if response.unit:
                response.unit.unit_id = generate_unit_id(response.unit.id)
            responses.append(response.model_dump(mode="json"))
        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/tenant/{tenant_id}", response_model=List[TenantRequestResponse])
async def get_requests_by_tenant(
    tenant_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        tenant = db.query(User).filter_by(id=tenant_id).first()
        if not tenant:
            return not_found_error(f"Tenant with ID {tenant_id} not found")

        requests = tenant_request_service.get_by_tenant(db, tenant_id, skip, limit)
        responses = []
        for r in requests:
            response = TenantRequestResponse.model_validate(r)
            if response.property and not response.property.property_id:
                response.property.property_id = generate_property_id(response.property.id)
            if response.unit:
                response.unit.unit_id = generate_unit_id(response.unit.id)
            responses.append(response.model_dump(mode="json"))
        return data_response(responses)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
