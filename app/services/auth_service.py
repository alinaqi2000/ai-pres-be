from sqlalchemy.orm import Session, joinedload

from database.models import User
from schemas.auth_schema import UserCreate, UserUpdate
from utils.dependencies import hash_password


def create_user(payload: UserCreate, db: Session, created_by_owner: bool = False, owner_id: int = None) -> User:
    user = User(
        name=payload.name,
        email=payload.email,
        city=payload.city,
        cnic=payload.cnic,
        gender=payload.gender,
        nature_of_business=payload.nature_of_business,
        hashed_password=hash_password(payload.password),
        is_active=True,
        booked_by_owner=created_by_owner,  # Set based on who creates the user
        created_by_owner_id=owner_id,  # Track which owner created this user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(email: str, db: Session):
    return db.query(User).filter_by(email=email).first()


def get_user_by_id(user_id: int, db: Session):
    return (
        db.query(User)
        .options(joinedload(User.roles))
        .filter(User.id == user_id)
        .first()
    )


def get_all_users(db: Session):
    return db.query(User).options(joinedload(User.roles)).all()


def update_user(user_id: int, payload: UserUpdate, db: Session):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None

    if payload.name:
        user.name = payload.name
    if payload.email:
        user.email = payload.email
    if payload.cnic is not None:
        user.cnic = payload.cnic
    if payload.gender is not None:
        user.gender = payload.gender
    if payload.nature_of_business is not None:
        user.nature_of_business = payload.nature_of_business
    if payload.city is not None:
        user.city = payload.city
    db.commit()
    db.refresh(user)

    return user


def delete_user(user_id: int, db: Session):
    user = get_user_by_id(user_id, db)
    if user:
        db.delete(user)
        db.commit()
    return user
