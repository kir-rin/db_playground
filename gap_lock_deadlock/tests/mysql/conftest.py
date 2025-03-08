import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gap_lock_deadlock.models import Base

# MySQL 연결 설정
DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/sql_tunning"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)  # 테이블 생성
    yield engine
    Base.metadata.drop_all(engine)  # 테스트 후 테이블 삭제


@pytest.fixture(scope="function")
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
