import random
import string
from database.models.user_model import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import traceback
from typing import List, Union

from schemas.auth_schema import (
    LoginRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordUpdate,
    ResponseModel,
)

from database.init import get_db

from utils.dependencies import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    owner_required,
)
from services.auth_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    delete_user,
    update_user,
)
from services.email_service import EmailService

from responses.success import data_response, empty_response
from responses.error import (
    unauthorized_error,
    conflict_error,
    not_found_error,
    internal_server_error,
    forbidden_error,
)


router = APIRouter(prefix="/auth", tags=["Auth"])

email_service = EmailService()


@router.post("/signup", response_model=ResponseModel)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(payload.email, db)
    if existing:
        return conflict_error("User already exists")

    try:
        user = create_user(payload, db)
        token = create_access_token({"sub": user.email})
        return data_response(
            {
                "access_token": token,
                "token_type": "bearer",
                "user": UserResponse.from_orm(user),
            }
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to register user: {str(e)}")


@router.post("/signin", response_model=ResponseModel)
def signin(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = get_user_by_email(credentials.email, db)
        if not user or not verify_password(credentials.password, user.hashed_password):
            return unauthorized_error("Invalid credentials")

        token = create_access_token({"sub": user.email})
        return data_response(
            {
                "access_token": token,
                "token_type": "bearer",
                "user": UserResponse.from_orm(user),
            }
        )

    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.post("/create-user", response_model=ResponseModel)
async def create_user_route(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(owner_required),
):
    """Route for owners to create tenant users"""
    try:

        user = create_user(payload, db, created_by_owner=True, owner_id=current_user.id)
        return data_response(UserResponse.from_orm(user))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to create user: {str(e)}")


@router.get("/my-users", response_model=ResponseModel)
def get_my_users(db: Session = Depends(get_db), current_user=Depends(owner_required)):
    """Route for owners to get all their tenants"""
    try:
        users = (
            db.query(User)
            .filter(
                User.booked_by_owner == True,
                User.created_by_owner_id == current_user.id,
            )
            .all()
        )
        return data_response([UserResponse.from_orm(user) for user in users])
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to retrieve users: {str(e)}")


@router.get("/me", response_model=Union[UserResponse, ResponseModel])
def get_user(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Route for any authenticated user to get their own information"""
    try:
        user = get_user_by_id(current_user.id, db)
        if not user:
            return not_found_error(f"No user found with id {current_user.id}")
        return data_response(UserResponse.from_orm(user))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to fetch user: {str(e)}")


@router.delete("/user/{user_id}", response_model=ResponseModel)
def delete_user_by_id(
    user_id: int, db: Session = Depends(get_db), current_user=Depends(owner_required)
):
    """Route for owners to delete their tenants"""
    try:
        user_to_delete = (
            db.query(User)
            .filter(User.id == user_id, User.booked_by_owner == True)
            .first()
        )

        if not user_to_delete:
            return forbidden_error(
                "You can only delete users that were created by property owners"
            )

        user = delete_user(user_id, db)
        if not user:
            return not_found_error(f"No user found with id {user_id}")
        return data_response(
            {"message": f"User with id {user_id} deleted successfully"}
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to delete user: {str(e)}")


@router.patch("/user/{user_id}", response_model=Union[ResponseModel, UserUpdate])
def update_user_by_id(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(owner_required),
):
    """Route for owners to update their tenants"""
    try:
        user_to_update = (
            db.query(User)
            .filter(User.id == user_id, User.booked_by_owner == True)
            .first()
        )

        if not user_to_update:
            return forbidden_error(
                "You can only update users that were created by property owners"
            )

        user = update_user(user_id, payload, db)
        if not user:
            return not_found_error(f"No user found with id {user_id}")
        return data_response(UserResponse.from_orm(user))
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(f"Failed to update user: {str(e)}")


@router.post("/reset-password", response_model=ResponseModel)
async def reset_password(
    email: str, db: Session = Depends(get_db), current_user=Depends(owner_required)
):
    """Route for owners to reset a tenant's password"""
    try:
        user = get_user_by_email(email, db)
        if not user:
            return not_found_error("User not found")

        if not user.booked_by_owner:
            return forbidden_error(
                "You can only reset passwords for users that were created by property owners"
            )

        new_password = "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )

        user.hashed_password = hash_password(new_password)
        db.commit()

        await email_service.send_new_password_email(email, new_password)

        return data_response(
            {"message": "Check your email for the new password"},
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


@router.patch("/password", response_model=ResponseModel)
async def update_password(
    payload: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Route for any authenticated user to update their own password"""
    try:
        if not verify_password(payload.current_password, current_user.hashed_password):
            return unauthorized_error("Current password is incorrect")

        current_user.hashed_password = hash_password(payload.new_password)
        db.commit()

        return data_response({"message": "Password updated successfully"})
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))
