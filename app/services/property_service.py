from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from database.models import Property as PropertyModel, Booking
from schemas.property_schema import PropertyCreate, Property
from services.base_service import BaseService
from sqlalchemy import func
from datetime import datetime, timezone

class PropertyService(BaseService):
    def __init__(self):
        super().__init__(PropertyModel)

    def create_property(
        self, db: Session, owner_id: int, property_in: PropertyCreate
    ) -> Property:
        property_in.owner_id = owner_id
        return self.create(db, property_in)

    def get_property(self, db: Session, property_id: int) -> Optional[Property]:
        property_obj = db.query(self.model).filter(self.model.id == property_id).first()
        if property_obj:
            db.commit() 
        return property_obj

    def get_properties(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 1000,
        is_occupied: Optional[bool] = None,
        city: Optional[str] = None,
        is_published: Optional[bool] = None,
        owner_id: Optional[int] = None, 
    ) -> List[Property]:
        query = db.query(self.model).options(joinedload(self.model.owner))
        if city:
            query = query.filter(func.lower(self.model.city).like(f"%{city.lower()}%"))
        if is_published is not None:
            query = query.filter(self.model.is_published == is_published)
        if is_occupied is not None:
            query = query.filter(self.model.is_occupied == is_occupied)
        if owner_id is not None:
            query = query.filter(self.model.owner_id == owner_id)
        
        properties = query.offset(skip).limit(limit).all()
        db.commit()  
        return properties

    def update_property(
        self, db: Session, property_id: int, property_in: PropertyCreate
    ) -> Optional[Property]:
        db_obj = self.get(db, property_id)
        if db_obj:
            return self.update(db, db_obj, property_in)
        return None

    def delete_property(self, db: Session, property_id: int) -> bool:
        return self.delete(db, property_id)

    def update_property_publish_status(
        self, db: Session, property_id: int, is_published: bool
    ) -> Optional[Property]:
        db_obj = self.get(db, property_id)
        if db_obj:
            db_obj.is_published = is_published
            db.commit()
            db.refresh(db_obj)
            return db_obj
        return None


    def get(self, db: Session, id: int) -> Optional[Property]:
        property_obj = db.query(self.model).filter(self.model.id == id).first()
        return property_obj

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Property]:
        properties = db.query(self.model).offset(skip).limit(limit).all()
        return properties
