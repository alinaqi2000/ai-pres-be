from sqlalchemy.orm import Session
from database.models.tenant_model import Tenant
from schemas.tenant_schema import TenantCreate
from database.models.user_model import User
from responses.error import not_found_error, conflict_error  # Added conflict_error


def create_tenant(db: Session, tenant: TenantCreate, owner_id: int):
    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner:
        return not_found_error("Owner not found")

    existing_tenant = (
        db.query(Tenant)
        .filter(Tenant.owner_id == owner_id, Tenant.email == tenant.email)
        .first()
    )

    if existing_tenant:
        return conflict_error(
            f"Tenant with email {tenant.email} already exists for this owner."
        )

    db_tenant = Tenant(
        name=tenant.name,
        email=tenant.email,
        phone_number=tenant.phone_number,
        owner_id=owner_id,
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def get_tenant_by_id(db: Session, tenant_id: int):
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenants_by_owner(db: Session, skip: int, limit: int, owner_id: int):
    return (
        db.query(Tenant)
        .filter(Tenant.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
