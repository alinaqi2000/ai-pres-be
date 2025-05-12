from config import DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
import os

class Base(DeclarativeBase):
    pass

engine = create_engine(DATABASE_URL)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        SessionLocal.remove()
