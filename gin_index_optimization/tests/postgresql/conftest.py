import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from gin_index_optimization.models import Base

# MySQL 연결 설정
DATABASE_URL = "postgresql+psycopg://postgres:root@localhost:5432/postgres"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION pg_trgm;"))
    Base.metadata.create_all(engine)  # 테이블 생성
    yield engine
    Base.metadata.drop_all(engine)  # 테스트 후 테이블 삭제
    with engine.begin() as conn:
        conn.execute(text("DROP EXTENSION pg_trgm;"))


@pytest.fixture(scope="function")
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
