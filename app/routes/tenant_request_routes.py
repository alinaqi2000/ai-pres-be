from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.models.tenant_request_model import TenantRequest
from database.models.property_model import Property, Floor, Unit
from database.models.user_model import User
from schemas.property_schema import PropertyCreate
from schemas.tenant_request_schema import (
    TenantRequestCreate,
    TenantRequestUpdate,
    TenantRequestOut,
)
from services.tenant_request_service import TenantRequestService
from utils.dependencies import get_current_user, get_db
from responses.success import data_response, empty_response
from responses.error import not_found_error, internal_server_error, conflict_error, forbidden_error

import traceback

router = APIRouter(prefix="/tenant_requests", tags=["Tenant Requests"])
tenant_request_service = TenantRequestService()


@router.post("/create_request", response_model=TenantRequestOut)
async def create_request(
    request: TenantRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user

    try:
        existing = (
            db.query(TenantRequest)
            .filter_by(tenant_id=current_user.id, unit_id=request.unit_id)
            .first()
        )
        if existing:
            return conflict_error("Tenant has already made a request for this unit.")

        property_exists = db.query(Property).filter_by(id=request.property_id).first()
        if not property_exists:
            return not_found_error(
                f"Property with id {request.property_id} does not exist"
            )

        floor_exists = db.query(Floor).filter_by(id=request.floor_id).first()
        if not floor_exists:
            return not_found_error(f"Floor with id {request.floor_id} does not exist")

        unit_exists = (
            db.query(Unit).filter_by(id=request.unit_id, is_occupied=False).first()
        )
        if not unit_exists:
            return not_found_error(f"Unit with id {request.unit_id} is not available")

        request.tenant_id = current_user.id
        created = tenant_request_service.create(db, request)
        return data_response(
            TenantRequestOut.model_validate(created).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/all_requests", response_model=List[TenantRequestOut])
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
                TenantRequestOut.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{request_id}", response_model=TenantRequestOut)
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
            TenantRequestOut.model_validate(request).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{request_id}", response_model=TenantRequestOut)
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

        # Access owner_id from the property associated with the tenant request
        if current_user.id == db_obj.property.owner_id:
            updated = tenant_request_service.update(db, db_obj, update_data)
            return data_response(
                TenantRequestOut.model_validate(updated).model_dump(mode="json")
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


@router.get("/property/{property_id}", response_model=List[TenantRequestOut])
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
                TenantRequestOut.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/tenant/{tenant_id}", response_model=List[TenantRequestOut])
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
                TenantRequestOut.model_validate(r).model_dump(mode="json")
                for r in requests
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
