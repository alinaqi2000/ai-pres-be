from typing import List, Optional
from sqlalchemy.orm import Session
from database.models.property_model import Unit as UnitModel
from schemas.property_schema import UnitCreate, Unit
from services.base_service import BaseService

class UnitService(BaseService):
    def __init__(self):
        super().__init__(UnitModel)

    def create_unit(self, db: Session, floor_id: int, unit_in: UnitCreate) -> Unit:
        return self.create(db, unit_in)

    def get_unit(self, db: Session, unit_id: int) -> Optional[Unit]:
        return self.get(db, unit_id)

    def get_units(self, db: Session, floor_id: int, skip: int = 0, limit: int = 100) -> List[Unit]:
        query = db.query(self.model).filter(self.model.floor_id == floor_id)
        return query.offset(skip).limit(limit).all()

    def update_unit(self, db: Session, unit_id: int, unit_in: UnitCreate) -> Optional[Unit]:
        db_obj = self.get(db, unit_id)
        if db_obj:
            return self.update(db, db_obj, unit_in)
        return None

    def delete_unit(self, db: Session, unit_id: int) -> bool:
        return self.delete(db, unit_id)