from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Floor as FloorModel
from schemas.property_schema import FloorCreate, Floor
from services.base_service import BaseService


def get_ordinal(num: int) -> str:
    """Convert a number to its ordinal form (1st, 2nd, 3rd, etc.)"""
    if 10 <= num % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")
    return f"{num}{suffix}"


class FloorService(BaseService):
    def __init__(self):
        super().__init__(FloorModel)

    def validate_floor(
        self,
        db: Session,
        property_id: int,
        floor_in: FloorCreate,
        exclude_floor_id: Optional[int] = None,
    ) -> None:
        """Validate if the floor can be created/updated with the given parameters"""
        # Check if ground floor already exists for this property
        if floor_in.number == 1 or (
            floor_in.name and floor_in.name.lower() in ["ground", "g", "gf"]
        ):
            existing_ground = (
                db.query(FloorModel)
                .filter(
                    FloorModel.property_id == property_id,
                    FloorModel.id != exclude_floor_id if exclude_floor_id else True,
                    (FloorModel.number == 1)
                    | (FloorModel.name != None)
                    & (func.lower(FloorModel.name).in_(["ground", "g", "gf"])),
                )
                .first()
            )
            if existing_ground:
                raise ValueError("Ground floor already exists for this property")

        # Check if basement floor already exists for this property
        if floor_in.number == 0 or (
            floor_in.name and floor_in.name.lower() in ["basement", "b", "bsmt", "bs"]
        ):
            existing_basement = (
                db.query(FloorModel)
                .filter(
                    FloorModel.property_id == property_id,
                    FloorModel.id != exclude_floor_id if exclude_floor_id else True,
                    (FloorModel.number == 0)
                    | (FloorModel.name != None)
                    & (
                        func.lower(FloorModel.name).in_(["basement", "b", "bsmt", "bs"])
                    ),
                )
                .first()
            )
            if existing_basement:
                raise ValueError("Basement floor already exists for this property")

        # Check if regular numbered floor already exists
        if floor_in.number > 0:
            existing_floor = (
                db.query(FloorModel)
                .filter(
                    FloorModel.property_id == property_id,
                    FloorModel.id != exclude_floor_id if exclude_floor_id else True,
                    FloorModel.number == floor_in.number,
                )
                .first()
            )
            if existing_floor:
                raise ValueError(
                    f"{existing_floor.name} already exists for this property"
                )

    def set_default_floor_name(self, floor_in: FloorCreate) -> None:
        """Set default name for the floor if not provided"""
        if floor_in.number == 1 and not floor_in.name:
            floor_in.name = "Ground Floor"
        elif floor_in.number == 0 and not floor_in.name:
            floor_in.name = "Basement"
        else:
            if not floor_in.name:
                ordinal_num = get_ordinal(floor_in.number - 1)
                floor_in.name = f"{ordinal_num} Floor"

    def create_floor(
        self, db: Session, property_id: int, floor_in: FloorCreate
    ) -> Floor:
        self.validate_floor(db, property_id, floor_in)
        self.set_default_floor_name(floor_in)
        floor_in.property_id = property_id
        return self.create(db, floor_in)

    def get_floor(self, db: Session, floor_id: int) -> Optional[Floor]:
        return self.get(db, floor_id)

    def get_floors(
        self, db: Session, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Floor]:
        query = db.query(self.model).filter(self.model.property_id == property_id)
        query = query.order_by(self.model.number.asc())
        return query.offset(skip).limit(limit).all()

    def update_floor(
        self, db: Session, floor_id: int, floor_in: FloorCreate
    ) -> Optional[Floor]:
        db_obj = self.get(db, floor_id)
        if not db_obj:
            return None

        # Get the property ID from the existing floor
        property_id = db_obj.property_id

        # Validate the update with the existing floor excluded from checks
        self.validate_floor(db, property_id, floor_in, exclude_floor_id=floor_id)

        # Set default name if not provided
        self.set_default_floor_name(floor_in)

        return self.update(db, db_obj, floor_in)

    def delete_floor(self, db: Session, floor_id: int) -> bool:
        return self.delete(db, floor_id)
