from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.models.request_model import TenantRequest
from database.models.property_model import Property
from database.models.user_model import User
from schemas.request_schema import (
    TenantRequestCreate,
    TenantRequestUpdate,
    TenantRequestOut,
)
from services.tenant_request_service import TenantRequestService
from utils.dependencies import get_db
from responses.success import data_response, empty_response
from responses.error import not_found_error, internal_server_error

import traceback

router = APIRouter(prefix="/tenant_requests", tags=["Tenant Requests"])
tenant_request_service = TenantRequestService()


@router.post("/create_request", response_model=TenantRequestOut)
async def create_request(request: TenantRequestCreate, db: Session = Depends(get_db)):
    try:
        property_exists = db.query(Property).filter_by(id=request.property_id).first()
        if not property_exists:
            return not_found_error(
                f"Property with id {request.property_id} does not exist"
            )

        tenant_exists = db.query(User).filter_by(id=request.tenant_id).first()
        if not tenant_exists:
            return not_found_error(f"Tenant with id {request.tenant_id} does not exist")

        created = tenant_request_service.create(db, request)
        return data_response(TenantRequestOut.from_orm(created).model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/all_requests", response_model=List[TenantRequestOut])
async def list_all_requests(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    try:
        requests = tenant_request_service.get_all(db, skip, limit)
        return data_response(
            [TenantRequestOut.from_orm(r).model_dump(mode="json") for r in requests]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/{request_id}", response_model=TenantRequestOut)
def get_request(request_id: int, db: Session = Depends(get_db)):
    try:
        request = tenant_request_service.get(db, request_id)
        if not request:
            return not_found_error(f"Tenant request with ID {request_id} not found")
        return data_response(TenantRequestOut.from_orm(request).model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/{request_id}", response_model=TenantRequestOut)
def update_request(
    request_id: int, update_data: TenantRequestUpdate, db: Session = Depends(get_db)
):
    try:
        db_obj = tenant_request_service.get(db, request_id)
        if not db_obj:
            return not_found_error(f"Tenant request with ID {request_id} not found")
        updated = tenant_request_service.update(db, db_obj, update_data)
        return data_response(TenantRequestOut.from_orm(updated).model_dump(mode="json"))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.delete("/{request_id}")
async def delete_request(request_id: int, db: Session = Depends(get_db)):
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
    property_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    try:
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            return not_found_error(f"Property with id {property_id} does not exist.")

        requests = tenant_request_service.get_by_property(db, property_id, skip, limit)
        return data_response(
            [TenantRequestOut.from_orm(r).model_dump(mode="json") for r in requests]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.get("/tenant/{tenant_id}", response_model=List[TenantRequestOut])
async def get_requests_by_tenant(
    tenant_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    try:
        tenant = db.query(User).filter_by(id=tenant_id).first()
        if not tenant:
            return not_found_error(f"Tenant with ID {tenant_id} not found")

        requests = tenant_request_service.get_by_tenant(db, tenant_id, skip, limit)
        return data_response(
            [TenantRequestOut.from_orm(r).model_dump(mode="json") for r in requests]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
