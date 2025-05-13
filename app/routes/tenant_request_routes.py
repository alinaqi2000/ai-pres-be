from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from typing import List

from database.models.tenant_request_model import TenantRequest
from database.models.property_model import Property, Floor, Unit
from database.models.user_model import User
from schemas.tenant_request_schema import (
    TenantRequestCreate,
    TenantRequestUpdate,
)
from schemas.tenant_request_response import TenantRequestResponse
from services.tenant_request_service import TenantRequestService
from utils.dependencies import get_current_user, get_db
from responses.success import data_response, empty_response
from responses.error import (
    not_found_error,
    internal_server_error,
    conflict_error,
    forbidden_error,
)

import traceback
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/tenant_requests", tags=["Tenant Requests"])
tenant_request_service = TenantRequestService()


@router.post("/create_request", response_model=TenantRequestResponse)
async def create_request(
    request: TenantRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        existing = tenant_request_service.check_existing_request(
            db, current_user.id, request
        )
        if existing:
            return conflict_error("Tenant has already made a request for this property.")

        if not request.unit_id:
            return conflict_error("unit_id is required to make a tenant request.")

        # Fetch Unit and its hierarchy (Floor, Property)
        unit_obj = (
            db.query(Unit)
            .options(
                selectinload(Unit.floor).selectinload(Floor.property)
            )
            .filter(Unit.id == request.unit_id)
            .first()
        )

        if not unit_obj:
            return not_found_error(f"Unit with ID {request.unit_id} not found.")
        
        if unit_obj.is_occupied: 
            return conflict_error(f"Unit with ID {request.unit_id} is currently occupied and not available for requests.")

        floor_obj = unit_obj.floor
        property_obj = floor_obj.property

        if not floor_obj:
             return internal_server_error(f"Critical: Floor not found for unit {unit_obj.id}. Data inconsistency.")
        if not property_obj:
             return internal_server_error(f"Critical: Property not found for floor {floor_obj.id}. Data inconsistency.")

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
            preferred_move_in=request.preferred_move_in,
            duration_months=request.duration_months,
        )
        
        existing_request = tenant_request_service.check_existing_request(
            db, current_user.id, actual_request_payload 
        )
        if existing_request:
            return conflict_error(
                "You have already made a request for this unit, or another pending/accepted request for you exists for this unit."
            )
        
        created_tenant_request = tenant_request_service.create(db, actual_request_payload)
        
        return data_response(
            TenantRequestResponse.model_validate(created_tenant_request).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"An unexpected error occurred: {str(e)}")


@router.get("/all_requests", response_model=List[TenantRequestResponse])
async def list_all_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        requests = tenant_request_service.get_all(db, skip, limit)
        return data_response(
            [
                TenantRequestResponse.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
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
        return data_response(
            TenantRequestResponse.model_validate(request).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{request_id}", response_model=TenantRequestResponse)
def update_request(
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
            updated = tenant_request_service.update(db, db_obj, update_data)
            return data_response(
                TenantRequestResponse.model_validate(updated).model_dump(mode="json")
            )
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
        return data_response(
            [
                TenantRequestResponse.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
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
        return data_response(
            [
                TenantRequestResponse.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
