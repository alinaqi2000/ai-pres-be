from sqlalchemy.orm import Session
from models.role_model import Role

from schemas.role_schema import RoleCreate, RoleUpdate

def create_role(payload: RoleCreate, db: Session):
    role = Role(**payload.dict())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def get_all_roles(db: Session):
    return db.query(Role).all()

def get_role_by_id(role_id: int, db: Session):
    return db.query(Role).filter(Role.id == role_id).first()

def update_role(role_id: int, payload: RoleUpdate, db: Session):
    role = get_role_by_id(role_id, db)
    if not role:
        return None
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(role, key, value)
    db.commit()
    db.refresh(role)
    return role

def delete_role(role_id: int, db: Session):
    role = get_role_by_id(role_id, db)
    if not role:
        return None
    db.delete(role)
    db.commit()
    return role
