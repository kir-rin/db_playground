from datetime import datetime, timedelta
import random
import pytest
from sqlalchemy.orm import Session

from multiple_column_indexes.models import Order


@pytest.fixture
def 테스트_주문(db_session: Session):
    statuses = ["pending", "shipped", "delivered", "cancelled"]
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    orders = [
        vars(
            Order(
                customer_id=random.randint(1, 10_000),
                order_date=start_date
                + timedelta(days=random.randint(0, (end_date - start_date).days)),
                product_id=random.randint(1, 10_000),
                quantity=random.randint(1, 10),
                status=random.choice(statuses),
            )
        )
        for _ in range(1, 1_000_000)
    ]

    db_session.bulk_insert_mappings(Order, orders)
    db_session.commit()
