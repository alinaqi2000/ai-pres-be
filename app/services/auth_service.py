from sqlalchemy.orm import Session, joinedload

from models.user_model import User
from schemas.auth_schema import UserCreate, UserUpdate
from utils.dependencies import hash_password


def create_user(payload: UserCreate, db: Session) -> User:
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
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
    if payload.password:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)

    return user


def delete_user(user_id: int, db: Session):
    user = get_user_by_id(user_id, db)
    if user:
        db.delete(user)
        db.commit()
    return user
