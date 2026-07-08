import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from app.database import get_redis
from app.redis_keys import queue_key, admit_key

router = APIRouter(
    prefix="/queue",
    tags=["queue"]
)

@router.post("/{train_id}/join")
async def join_queue(train_id: str, redis: Redis = Depends(get_redis)):
    """ 대기열 등록, 로그인 여부 체크(x), 신원 확인 예매 단계에서 진행 """
    token = str(uuid.uuid4())
    score = time.time() #먼저 요청할수록 작은 값 (ZSET 자동으로 앞쪽 위치)

    await redis.zadd(queue_key(train_id), {token:score})

    return {"token": token}

@router.get("/{train_id}/status")
async def queue_statue(train_id: str, token:str, redis: Redis = Depends(get_redis)):
    """ 
        폴링용 엔드포인트, 클라이언트가 1~2초 마다 호출해서 자기 순번 확인 

        - WAITING: 대기열 (순번 정보 포함)
        - ADMITTED: 입장 (예매 API 호출 가능)
        - 404 : X
    """
    key = queue_key(train_id)

    rank = await redis.zrank(key, token)
    if rank is not None:
        total = await redis.zcard(key)
        return {
            "state": "WAITING",
            "rank": rank + 1,       #ZRANK 0부터 시작
            "ahead_of_me": rank,    #내 앞에 대기중인 인원
            "total_waiting": total, #전체 대기 인원
        }
    
    # 대기열 x -> 입장 처리 admit 키로 옮겨갔는지 확인 
    ttl = await redis.ttl(admit_key(token)) 
    if ttl and ttl > 0:
        return {
            "state": "ADMITTED",
            "expires_in_seconds": ttl,
        }
    
    raise HTTPException(status_code=404, detail="유효하지 않은 토큰 입니다")