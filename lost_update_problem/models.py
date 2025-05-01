from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    balance = Column(Integer)


class AccountWithVersion(Base):
    __tablename__ = "account_with_version"

    id = Column(Integer, primary_key=True)
    balance = Column(Integer)
    version_id = Column(Integer, nullable=False)

    __mapper_args__ = {"version_id_col": version_id}
