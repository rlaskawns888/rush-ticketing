""" 키 네이밍 공통 모듈 """

def queue_key(train_id: str) -> str:
    """대기열 ZSET 키: queue:{train_id}"""
    """  Redis: queue:{train_id} 열차마다 독립된 대기열을 갖도록 """
    return f"queue:{train_id}"


def admit_key(token: str) -> str:
    """입장 토큰 키: admit:{token} (TTL과 함께 저장됨)"""
    return f"admit:{token}"