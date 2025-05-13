from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.init import get_db
from database.models.user_model import User     
from schemas.tenant_schema import TenantCreate, TenantResponse
from services import tenant_service
from utils.dependencies import get_current_user
from responses.success import data_response
from responses.error import internal_server_error, not_found_error
import traceback

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("/create_tenant", response_model=TenantResponse)
def create_new_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new tenant associated with the currently authenticated owner."""
    try:
        tenant = tenant_service.create_tenant(db=db, tenant=payload, owner_id=current_user.id)
        if isinstance(tenant, dict) and tenant.get("status_code") == 404:   
            return not_found_error(tenant.get("detail"))
        if not tenant:
            return internal_server_error("Failed to create tenant")
        return tenant 
    except HTTPException as http_exc:
       return http_exc
    except Exception as e:
        return internal_server_error(f"An error {e} occurred while creating the tenant.")

@router.get("/get_by_owner", response_model=List[TenantResponse])
def get_my_tenants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not isinstance(current_user, User):
        return current_user
    try:
        tenants = tenant_service.get_tenants_by_owner(db, skip, limit, current_user.id)
        if not tenants:
            return not_found_error("No tenants found for this owner.")
        return data_response(
            [
                TenantResponse.model_validate(t).model_dump(mode="json")
                for t in tenants
            ]
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
    
    
@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant_by_id(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):    
    if not isinstance(current_user, User):
        return current_user
    try:
        tenant = tenant_service.get_tenant_by_id(db, tenant_id)
        if not tenant or tenant.owner_id != current_user.id:
            return not_found_error("Tenant not found.")
        return data_response(
            TenantResponse.model_validate(tenant).model_dump(mode="json")
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
        