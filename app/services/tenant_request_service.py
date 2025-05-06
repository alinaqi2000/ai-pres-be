from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from database.models.tenant_request_model import TenantRequest
from schemas.tenant_request_schema import TenantRequestCreate, TenantRequestUpdate
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

    def get(self, db: Session, request_id: int) -> Optional[TenantRequest]:
        return (
            db.query(TenantRequest)
            .options(
                joinedload(TenantRequest.tenant),
                joinedload(TenantRequest.property),
                joinedload(TenantRequest.floor),
                joinedload(TenantRequest.unit),
            )
            .filter(TenantRequest.id == request_id)
            .first()
        )

    def get_all(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[TenantRequest]:
        return (
            db.query(TenantRequest)
            .options(
                joinedload(TenantRequest.tenant),
                joinedload(TenantRequest.property),
                joinedload(TenantRequest.floor),
                joinedload(TenantRequest.unit),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

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
            .options(
                joinedload(self.model.tenant),
                joinedload(self.model.property),
                joinedload(self.model.floor),
                joinedload(self.model.unit),
            )
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
            .options(
                joinedload(self.model.tenant),
                joinedload(self.model.property),
                joinedload(self.model.floor),
                joinedload(self.model.unit),
            )
            .filter(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
