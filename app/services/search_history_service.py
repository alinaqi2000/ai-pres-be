from sqlalchemy.orm import Session
from database.models.search_history_model import SearchHistory
from schemas.search_history_schema import SearchHistoryCreate
from database.models.user_model import User
from typing import Optional

def create_search_history(db: Session, search_data: SearchHistoryCreate) -> SearchHistory:
    db_obj = SearchHistory(**search_data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_user_search_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(SearchHistory).filter(SearchHistory.user_id == user_id).order_by(SearchHistory.created_at.desc()).offset(skip).limit(limit).all()
