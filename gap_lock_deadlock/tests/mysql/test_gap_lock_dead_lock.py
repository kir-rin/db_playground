import threading

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


def test_gap_lock_dead_lock(engine):
    """
    Flow:
        1. t1이 갭 락을 획득
        2. t2가 갭 락을 획득
        3. t1은 insert시 t2의 갭 락에 의해 대기
        4. t2는 update시 t1의 갭 락에 의해 대기
        5. 데드락 발생
    """
    Session = sessionmaker(bind=engine)

    # 이벤트를 사용해 스레드 간 동기화
    t1_acquired_gap_lock = threading.Event()  # t1이 갭 락을 획득했음을 알림
    t2_acquired_gap_lock = threading.Event()  # t2가 갭 락을 획득했음을 알림

    # 테스트에 사용할 쿼리
    select_for_update_query = (
        "SELECT * FROM t1 WHERE index_column = '{index_name}' FOR UPDATE;"
    )
    insert_query = "INSERT INTO t1 (id, index_column, c1) VALUES (1, 'index1', 1);"
    update_query = "UPDATE t1 SET index_column = 'index1', c1 = 1 WHERE id = 1;"

    def session1_func():
        session = Session()
        try:
            session.begin()
            print("Session 1: Acquiring gap lock with SELECT FOR UPDATE")
            # 갭 락 획득 (index_column = 'index1'인 레코드가 없으므로 갭 락 발생)
            session.execute(text(select_for_update_query.format(index_name="index1")))
            # t1이 갭 락을 획득했음을 알림
            t1_acquired_gap_lock.set()

            # t2가 갭 락을 획득할 때까지 대기
            t2_acquired_gap_lock.wait(timeout=10)
            # INSERT 시도 (t2의 갭 락에 의해 대기 상태가 됨)
            session.execute(text(insert_query))
            print("Session 1: Committing")
            session.commit()
        except Exception as e:
            print("Session 1 error:", e)
        finally:
            session.close()
            print("Session 1: Closed")

    def session2_func():
        session = Session()
        try:
            # t1이 갭 락을 획득할 때까지 대기
            t1_acquired_gap_lock.wait(timeout=10)

            session.begin()
            print("Session 2: Acquiring gap lock with SELECT FOR UPDATE")
            # 갭 락 획득 (다른 범위의 갭 락)
            session.execute(text(select_for_update_query.format(index_name="index2")))
            # t2가 갭 락을 획득했음을 알림
            t2_acquired_gap_lock.set()

            print("Session 2: Attempting INSERT")
            # INSERT 시도 (t1의 갭 락과 충돌하여 데드락 발생)
            session.execute(text(update_query))

            print("Session 2: Committing")
            session.commit()
        except Exception as e:
            print("Session 2 error:", e)
        finally:
            session.close()
            print("Session 2: Closed")

    # 스레드 생성 및 시작
    t1 = threading.Thread(target=session1_func)
    t2 = threading.Thread(target=session2_func)

    t1.start()
    t2.start()

    # 스레드 종료 대기
    t1.join(timeout=30)  # 최대 30초 대기
    t2.join(timeout=30)  # 최대 30초 대기

    # 테스트 결과 확인
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM t1")).fetchall()
        print("Final table content:", result)
