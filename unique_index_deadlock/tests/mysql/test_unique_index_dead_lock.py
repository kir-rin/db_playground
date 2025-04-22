import time
import threading

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


def session1_func(Session, start_event, rollback_event):
    session = Session()
    session.begin()
    # 세션1이 먼저 INSERT 실행
    session.execute(text("INSERT INTO t1 VALUES (1)"))
    # 세션2, 3에게 진행 준비가 됐음을 알림
    start_event.set()
    # 세션2와 3이 INSERT 시도 후 대기 중일 것으로 가정하고, 일정 시간 후 롤백 신호까지 대기
    rollback_event.wait()
    session.execute(text("ROLLBACK"))
    session.close()


def session2_func(Session, start_event):
    # 세션1이 INSERT한 후에 시작하도록 대기
    start_event.wait()
    session = Session()
    session.begin()
    try:
        session.execute(text("INSERT INTO t1 VALUES (1)"))
    except Exception as e:
        print("Session2 insert error:", e)
    try:
        session.commit()
    except Exception as e:
        print("Session2 commit error:", e)
    session.close()


def session3_func(Session, start_event):
    start_event.wait()
    session = Session()
    session.begin()
    error = None
    try:
        session.execute(text("INSERT INTO t1 VALUES (1)"))
    except Exception as e:
        print("Session3 insert error:", e)
    try:
        session.commit()
    except Exception as e:
        print("Session3 commit error:", e)
        error = e
    session.close()
    return error


def test_unique_index_dead_lock(engine):
    """
    Flow:
        1. t1이 x-lock 획득
        2. t2, t3가 write 시도 후 실패
        3. t2, t3가 unique index 를 읽기 위해 s-lock 획득
        4. t1이 rollback
        5. t2, t3가 서로 기다리고 있어서 deadlock 발생
    """
    Session = sessionmaker(bind=engine)
    # 이벤트를 사용해 동시성을 제어합니다.
    start_event = threading.Event()  # 세션1이 INSERT 완료 시점을 알림
    rollback_event = threading.Event()  # 세션1 롤백 신호

    # 각 세션을 별도 스레드에서 실행
    t1 = threading.Thread(
        target=session1_func, args=(Session, start_event, rollback_event)
    )
    t2 = threading.Thread(target=session2_func, args=(Session, start_event))
    t3 = threading.Thread(target=session3_func, args=(Session, start_event))

    t1.start()
    t2.start()
    t3.start()

    # 세션1이 INSERT를 수행하고 세션2,3이 INSERT 시도를 시작할 시간을 확보하기 위해 잠시 대기
    time.sleep(2)
    # 이제 세션1에 롤백을 수행하도록 신호를 보냅니다.
    rollback_event.set()

    t1.join()
    t2.join()
    t3.join()

    # 최종적으로 테이블의 상태를 확인합니다.
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM t1")).fetchall()
        print("Final table content:", result)
