import asyncio

from redis.asyncio import Redis, from_url

from app.config import settings
from app.redis_keys import queue_key, admit_key


TRAIN_ID = "train-001"

#cd backend
#poetry run python -m scheduler.main


async def admit_next_batch(redis: Redis, train_id: str) -> int:
    """ 대기열 맨 앞에서 설정된 인원만큼 꺼내, 각자에게 입장 토큰 발급 """
    popped = await redis.zpopmin(queue_key(train_id), settings.admit_batch_size)
    if not popped:
        return 0
    
    for token, _score in popped:
        await redis.set( 
            admit_key(token),
            train_id,
            ex=settings.admit_ttl_seconds
        )
    
    return len(popped)


async def main():
    redis: Redis = from_url(settings.redis_url, decode_responses=True)
    print(f"[scheduler] started. batch={settings.admit_batch_size}/sec, ttl={settings.admit_ttl_seconds}s")

    while True:
        admitted_count = await admit_next_batch(redis, TRAIN_ID)
        
        if admitted_count > 0:
            print(f"[scheduler] admitted {admitted_count} users")

            await asyncio.sleep(1)
    

if __name__ == "__main__":
    asyncio.run(main())
    
        