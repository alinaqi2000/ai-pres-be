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
    UserOut,
    UserUpdate,
    PasswordUpdate,
    ResponseModel,
)

from database.init import get_db
from utils.dependencies import hash_password, verify_password, create_access_token, get_current_user
from services.auth_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    delete_user,
    update_user,
)
from services.email_service import EmailService

from responses.success import success_response
from responses.error import (
    unauthorized_error,
    conflict_error,
    not_found_error,
    internal_server_error,
)


router = APIRouter(prefix="/auth", tags=["Auth"])

email_service = EmailService()

# ------------------ SIGN UP ------------------


@router.post("/signup", response_model=ResponseModel)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(payload.email, db)
    if existing:
        return conflict_error("User already exists")

    try:
        user = create_user(payload, db)
        token = create_access_token({"sub": user.email})
        return success_response(
            "Registration successful", {"access_token": token, "token_type": "bearer"}
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to register user", str(e))


# ------------------ SIGN IN ------------------


@router.post("/signin", response_model=ResponseModel)
def signin(credentials: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = get_user_by_email(credentials.email, db)
        if not user or not verify_password(credentials.password, user.hashed_password):
            return unauthorized_error("Invalid credentials")

        token = create_access_token({"sub": user.email})
        return success_response(
            "Login successful", {"access_token": token, "token_type": "bearer"}
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to login", str(e))


# ------------------ GET ALL USERS ------------------


@router.get("/get_all", response_model=List[UserOut])
def get_all_users_endpoint(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        return get_all_users(db)
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to retrieve users", str(e))


# ------------------ GET USER BY ID ------------------


@router.get("/user/{user_id}", response_model=Union[UserOut, ResponseModel])
def get_user(
    user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        user = get_user_by_id(user_id, db)
        if not user:
            return not_found_error(f"No user found with id {user_id}")
        return user
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to fetch user", str(e))


# ------------------ DELETE USER BY ID ------------------

@router.delete("/user/{user_id}", response_model=ResponseModel)
def delete_user_by_id(
    user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user

    try:
        user = get_user_by_id(user_id, db)
        if user:
            db.delete(user)
            db.commit()
        return success_response(message=f"User with id {user_id} deleted successfully")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to delete user", str(e))


# ------------------ Update USER BY ID ------------------


@router.patch("/user/{user_id}", response_model=Union[ResponseModel, UserUpdate])
def update_user_route(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user = update_user(user_id, payload, db)
        if not user:
            return not_found_error(f"No user found with id {user_id}")
        return success_response(
            "User updated successfully",
            {
                "name": payload.name,
                "email": payload.email,
                "password": payload.password,
            },
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to update user", str(e))


# ------------------ PASSWORD RESET ------------------

@router.post("/reset-password", response_model=ResponseModel)
async def reset_password(email: str, db: Session = Depends(get_db)):
    try:
        user = get_user_by_email(email, db)
        if not user:
            return not_found_error("User not found")

        # Generate a new 8-character alphanumeric password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Update user's password
        user.hashed_password = hash_password(new_password)
        db.commit()
        
        # Send the new password to user's email
        await email_service.send_new_password_email(email, new_password)
        
        return success_response(
            "Password reset successfully",
            {"message": "Check your email for the new password"}
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))


# ------------------ UPDATE PASSWORD ------------------

@router.patch("/password", response_model=ResponseModel)
async def update_password(
    payload: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not isinstance(current_user, User):
        return current_user

    try:
        # Verify current password
        if not verify_password(payload.current_password, current_user.hashed_password):
            return unauthorized_error("Current password is incorrect")

        # Update password
        current_user.hashed_password = hash_password(payload.new_password)
        db.commit()
        db.refresh(current_user)

        return success_response(
            "Password updated successfully",
            {"message": "Password has been updated"}
        )
    except Exception as e:
        traceback.print_exc()
        return internal_server_error(str(e))

# ------------------ DELETE USER BY ID ------------------

@router.delete("/{user_id}", response_model=ResponseModel)
def delete_user_by_id(
    user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    try:
        deleted_user = delete_user(user_id, db)
        if not deleted_user:
            return not_found_error(f"No user found with id {user_id}")
        return success_response(message=f"User with id {user_id} deleted successfully")
    except Exception as e:
        traceback.print_exc()
        return internal_server_error("Failed to delete user", str(e))


