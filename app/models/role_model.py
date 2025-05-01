from database.init import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")
