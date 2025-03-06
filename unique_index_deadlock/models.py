from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class T(Base):
    __tablename__ = "t1"

    id = Column(Integer, primary_key=True)
