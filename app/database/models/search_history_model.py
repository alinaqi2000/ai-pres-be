from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import timezone
from database.init import Base
from database.models.user_model import User

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    query_name = Column(String(100), nullable=True)
    query_city = Column(String(100), nullable=True)
    monthly_rent_gt = Column(Float, nullable=True)
    monthly_rent_lt = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship('User', back_populates='search_histories')

