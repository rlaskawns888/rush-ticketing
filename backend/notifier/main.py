import asyncio
 
from redis.asyncio import Redis, from_url
from sqlalchemy import select, update
 
from app.config import settings
from app.database import async_session_factory
from app.models import Train, Seat, Reservation, ReservationStatus

# db 0번을 쓰고 있으므로(REDIS_URL의 /0) 채널명도 0번 기준
EXPIRED_CHANNEL = "__keyevent@0__:expired"

async def handle_expired_key(key: str) -> None:
    """
    - 만료된 키 이름을 받아서, hold:{train_code}:{seat_number} 형태인지
    확인하고 맞으면 DB 예약상태 EXPIRED 로 갱신

    - admit:{token} 같은 다른 TTL 키의 만료 알림도 같은 채널로 오므로 걸러내야함
    """
    parts = key.split(":")
    if len(parts) != 3 or parts[0] != "hold":
        return 
    
    _, train_code, seat_number = parts

    async with async_session_factory() as session:
        train = await session.scalar(select(Train).where(Train.code == train_code))
        if train is None:
            return
        
        seat = await session.scalar(
            select(Seat).where(Seat.train_id == train.id, Seat.seat_number == seat_number)
        )
        if seat is None:
            return

        # HELD 상태인 예약만 EXPIRED 변경
        result = await session.execute(
            update(Reservation)
             .where(Reservation.seat_id == seat.id, Reservation.status == ReservationStatus.HELD)
             .values(status = ReservationStatus.EXPIRED)
        )
        await session.commit()

        if result.rowcount > 0:
            print(f"[notifier] 좌석 {seat_number} hold 만료 -> DB 상태 EXPIRED로 갱신")

async def main() -> None:
    redis: Redis = from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(EXPIRED_CHANNEL)

    print(f"[notifier] started, listening to {EXPIRED_CHANNEL}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            # subscribe 확인 메시지 등은 건너뜀, 실제 이벤트만 처리
            continue

        expired_key = message["data"]
        await handle_expired_key(expired_key)

if __name__ == "__main__":
    asyncio.run(main())