from sqlalchemy import text
from sqlalchemy.orm import Session
import pprint

from gin_index_optimization.fixture import 테스트


# Reference : PostgreSQL GIN 인덱스를 통한 LIKE 검색 성능 개선 (https://medium.com/vuno-sw-dev/postgresql-gin-%EC%9D%B8%EB%8D%B1%EC%8A%A4%EB%A5%BC-%ED%86%B5%ED%95%9C-like-%EA%B2%80%EC%83%89-%EC%84%B1%EB%8A%A5-%EA%B0%9C%EC%84%A0-3c6b05c7e75f)
def test_gin_index_optimization_with_trgm(db_session: Session, 테스트):
    query_with_like = """
        EXPLAIN (FORMAT JSON) SELECT * FROM t1 where t1.{column} LIKE '%{string}%';
    """
    result = db_session.execute(
        text(query_with_like.format(column="s1_with_gin_index", string="abcd"))
    )
    execution_plan_with_gin_index = result.mappings().first()["QUERY PLAN"][0]
    pprint.pp(execution_plan_with_gin_index)

    result = db_session.execute(
        text(query_with_like.format(column="s2_with_btree_index", string="abcd"))
    )
    execution_plan_with_btree_index = result.mappings().first()["QUERY PLAN"][0]
    pprint.pp(execution_plan_with_btree_index)

    assert (
        execution_plan_with_gin_index["Plan"]["Plans"][0]["Node Type"]
        == "Bitmap Index Scan"
    )
    assert (
        execution_plan_with_btree_index["Plan"]["Plans"][0]["Node Type"] == "Seq Scan"
    )

    # pg_trgm은 컬럼의 값을 3글자씩 쪼개서 인덱싱에 사용하므로,
    # 문자열이 세 글자 미만일 때는 gin index가 적용되지 않음
    result = db_session.execute(
        text(query_with_like.format(column="s1_with_gin_index", string="ab"))
    )
    execution_plan_with_two_char_query = result.mappings().first()["QUERY PLAN"][0]
    pprint.pp(execution_plan_with_two_char_query)

    assert execution_plan_with_two_char_query["Plan"]["Node Type"] == "Seq Scan"
