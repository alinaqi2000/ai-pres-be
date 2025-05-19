from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SearchHistoryBase(BaseModel):
    query_name: Optional[str] = None
    query_city: Optional[str] = None
    monthly_rent_gt: Optional[float] = None
    monthly_rent_lt: Optional[float] = None


class SearchHistoryCreate(SearchHistoryBase):
    user_id: Optional[int] = None


class SearchHistoryResponse(SearchHistoryBase):
    id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True
