import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from app.database import get_redis

router = APIRouter(
    prefix="/queue",
    tags=["queue"]
)

def queue_key(train_id: str) -> str:
    """  Redis: queue:{train_id} 열차마다 독립된 대기열을 갖도록 """
    return f"queue:{train_id}"

@router.post("/{train_id}/join")
async def join_queue(train_id: str, redis: Redis = Depends(get_redis)):
    """ 대기열 등록, 로그인 여부 체크(x), 신원 확인 예매 단계에서 진행 """
    token = str(uuid.uuid4())
    score = time.time() #먼저 요청할수록 작은 값 (ZSET 자동으로 앞쪽 위치)

    await redis.zadd(queue_key(train_id), {token:score})

    return {"token": token}

@router.get("/{train_id}/status")
async def queue_statue(train_id: str, token:str, redis: Redis = Depends(get_redis)):
    """ 폴링용 엔드포인트, 클라이언트가 1~2초 마다 호출해서 자기 순번 확인 """
    key = queue_key(train_id)

    rank = await redis.zrank(key, token)
    if rank is None:
        #대기열에 없다는 건
        # (1) 아직  join을 안했거나, 
        # (2) 이미 입장처리 되어서 대기열에서 빠졌거나
        raise HTTPException(status_code=404, detail="대기열에 없는 토큰입니다(입장 or 만료)")
    
    total = await redis.zcard(key)

    return {
        "rank": rank + 1,       #ZRANK 0부터 시작
        "ahead_of_me": rank,    #내 앞에 대기중인 인원
        "total_waiting": total, #전체 대기 인원
    }