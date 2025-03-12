import random
import string
import pytest
from sqlalchemy.orm import Session

from .models import T


@pytest.fixture
def 테스트(db_session: Session):
    def make_random_string(length):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    objects = [
        vars(
            T(
                s1_with_gin_index=make_random_string(10),
                s2_with_btree_index=make_random_string(10),
            )
        )
        for _ in range(1, 1_000_000)
    ]
    db_session.bulk_insert_mappings(T, objects)
    db_session.commit()
