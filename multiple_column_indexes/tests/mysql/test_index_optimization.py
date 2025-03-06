from sqlalchemy import text
from sqlalchemy.orm import Session

from multiple_column_indexes.tests.fixture import 테스트_주문


# Reference : MySQL 성능 최적화 강의 (https://www.inflearn.com/course/mysql-%EC%84%B1%EB%8A%A5-%EC%B5%9C%EC%A0%81%ED%99%94/dashboard)
def test_index_optimization(db_session: Session, 테스트_주문):
    execution_plan_query = """
    EXPLAIN SELECT * FROM orders
    WHERE customer_id = 3905
        AND product_id = 968
        AND status = 'shipped'
        AND order_date > '2024-01-01';
    """

    # 쿼리 튜닝 전
    db_session.execute(
        text("""
    CREATE INDEX idx_order_date_customer_id ON orders(order_date, customer_id);
    """)
    )  # 카디널리티가 낮은 컬럼(order_date) 인덱스의 선행 컬럼으로 지정

    result = db_session.execute(text(execution_plan_query))
    execution_plan_before_tuning = result.mappings().first()

    # 쿼리 튜닝 후
    db_session.execute(
        text("""
    CREATE INDEX idx_customer_id_order_date ON orders(customer_id, order_date);
    """)
    )  # 카디널리티가 높은 컬럼(customer_id)을 인덱스의 선행 컬럼으로 지정
    result = db_session.execute(text(execution_plan_query))
    execution_plan_after_tuning = result.mappings().first()

    assert execution_plan_before_tuning["type"] == "ALL"
    assert execution_plan_after_tuning["type"] == "range"
    assert execution_plan_before_tuning["rows"] > execution_plan_after_tuning["rows"]
