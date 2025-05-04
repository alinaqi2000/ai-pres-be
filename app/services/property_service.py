from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from database.models.property_model import Property as PropertyModel
from schemas.property_schema import PropertyCreate, Property
from services.base_service import BaseService

class PropertyService(BaseService):
    def __init__(self):
        super().__init__(PropertyModel)

    def create_property(self, db: Session, owner_id: int, property_in: PropertyCreate) -> Property:
        property_in.owner_id = owner_id
        return self.create(db, property_in)

    def get_property(self, db: Session, property_id: int) -> Optional[Property]:
        return self.get(db, property_id)

    def get_properties(self, db: Session, skip: int = 0, limit: int = 100, city: Optional[str] = None, is_published: Optional[bool] = None, owner_id: Optional[int] = None) -> List[Property]:
        query = db.query(self.model).options(joinedload(self.model.owner))
        if city:
            query = query.filter(self.model.city == city)
        if is_published is not None:
            query = query.filter(self.model.is_published == is_published)
        if owner_id is not None:
            query = query.filter(self.model.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    def update_property(self, db: Session, property_id: int, property_in: PropertyCreate) -> Optional[Property]:
        db_obj = self.get(db, property_id)
        if db_obj:
            return self.update(db, db_obj, property_in)
        return None

    def delete_property(self, db: Session, property_id: int) -> bool:
        return self.delete(db, property_id)

    def update_property_publish_status(self, db: Session, property_id: int, is_published: bool) -> Optional[Property]:
        db_obj = self.get(db, property_id)
        if db_obj:
            db_obj.is_published = is_published
            db.commit()
            db.refresh(db_obj)
            return db_obj
        return None


