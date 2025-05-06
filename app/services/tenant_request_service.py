from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.request_model import TenantRequest
from schemas.request_schema import TenantRequestCreate, TenantRequestUpdate
from services.base_service import BaseService


class TenantRequestService:
    def __init__(self):
        self.model = TenantRequest

    def create(self, db: Session, obj_in: TenantRequestCreate) -> TenantRequest:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[TenantRequest]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(
        self, db: Session, db_obj: TenantRequest, obj_in: TenantRequestUpdate
    ) -> TenantRequest:
        for key, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        db_obj = self.get(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False

    def get_by_property(
        self, db: Session, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(self.model)
            .filter(self.model.property_id == property_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_tenant(
        self, db: Session, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(self.model)
            .filter(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
