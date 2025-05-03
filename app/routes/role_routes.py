from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import traceback
from typing import List, Union

from database.init import get_db
from database.models.role_model import Role
from schemas.role_schema import RoleCreate, RoleUpdate, ResponseModel, RoleOut
from utils.dependencies import get_current_user
from services.role_service import (
    create_role,
    get_all_roles,
    get_role_by_id,
    update_role,
    delete_role,
)

from responses.success import data_response
from responses.error import (
    conflict_error,
    not_found_error,
    internal_server_error
)

router = APIRouter(prefix="/roles", tags=["Roles"])

# ------------------ CREATE ROLE ------------------


@router.post("/create_role", response_model=ResponseModel)
def create_role_route(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        role = create_role(payload, db)
        return data_response(RoleOut.from_orm(role))
    except IntegrityError:
        db.rollback()
        return conflict_error("Role with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to create role", str(e))


# ------------------ GET ALL ROLES ------------------


@router.get("/get_all_role", response_model=List[RoleCreate])
def get_roles_route(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        roles = get_all_roles(db)
        return data_response(data=roles)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to retrieve roles", str(e))


# ------------------ GET ROLE BY ID ------------------


@router.get("/{role_id}", response_model=Union[RoleCreate, ResponseModel])
def get_role_by_id_route(
    role_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        role = get_role_by_id(role_id, db)
        if not role:
            return not_found_error(f"No role found with id {role_id}")
        return data_response(RoleOut.from_orm(role))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to retrieve role", str(e))


# ------------------ UPDATE ROLE ------------------


@router.patch("/{role_id}", response_model=ResponseModel)
def update_role_route(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        updated_role = update_role(role_id, payload, db)
        if not updated_role:
            return not_found_error(f"No role found with id {role_id}")
        return data_response(RoleOut.from_orm(updated_role))
    except IntegrityError:
        db.rollback()
        return conflict_error("Role with this name already exists")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to update role", str(e))


# ------------------ DELETE ROLE ------------------


@router.delete("/{role_id}", response_model=ResponseModel)
def delete_role_route(
    role_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        deleted = delete_role(role_id, db)
        if not deleted:
            return not_found_error(f"No role found with id {role_id}")
        return success_response(f"Role with id {role_id} deleted successfully")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to delete role", str(e))
