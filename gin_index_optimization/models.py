from sqlalchemy import Column, Index, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class T(Base):
    __tablename__ = "t1"

    id = Column(Integer, primary_key=True)
    s1_with_gin_index = Column(String(length=50))
    s2_with_btree_index = Column(String(length=50), index=True)

    __table_args__ = (
        Index(
            "gin_name_idx",
            s1_with_gin_index,
            postgresql_ops={"s1_with_gin_index": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )
