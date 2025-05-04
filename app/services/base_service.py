from typing import Type, TypeVar, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class BaseService:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, obj_in) -> ModelType:
        """
        Create a new record in the database
        
        Args:
            db: Database session
            obj_in: Either a SQLAlchemy model or a Pydantic schema
            
        Returns:
            The created model instance
        """
        if isinstance(obj_in, BaseModel):
            # If input is a Pydantic schema, create a new SQLAlchemy model
            db_obj = self.model(**obj_in.model_dump())
        else:
            # If input is already a SQLAlchemy model, use it directly
            db_obj = obj_in
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_by_model(self, db: Session, obj_in: ModelType) -> ModelType:
        db_obj = obj_in
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
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
