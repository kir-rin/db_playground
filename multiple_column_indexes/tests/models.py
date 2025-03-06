from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer)
    order_date = Column(DateTime)
    product_id = Column(Integer)
    quantity = Column(Integer)
    status = Column(String(length=50))
