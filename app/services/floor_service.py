from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.property_model import Floor as FloorModel
from schemas.property_schema import FloorCreate, Floor
from services.base_service import BaseService

class FloorService(BaseService):
    def __init__(self):
        super().__init__(FloorModel)

    def create_floor(self, db: Session, property_id: int, floor_in: FloorCreate) -> Floor:
        return self.create(db, floor_in)

    def get_floor(self, db: Session, floor_id: int) -> Optional[Floor]:
        return self.get(db, floor_id)

    def get_floors(self, db: Session, property_id: int, skip: int = 0, limit: int = 100) -> List[Floor]:
        query = db.query(self.model).filter(self.model.property_id == property_id)
        return query.offset(skip).limit(limit).all()

    def update_floor(self, db: Session, floor_id: int, floor_in: FloorCreate) -> Optional[Floor]:
        db_obj = self.get(db, floor_id)
        if db_obj:
            return self.update(db, db_obj, floor_in)
        return None

    def delete_floor(self, db: Session, floor_id: int) -> bool:
        return self.delete(db, floor_id)
