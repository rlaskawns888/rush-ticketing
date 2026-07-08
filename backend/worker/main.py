import asyncio
import json
from datetime import datetime
 
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.config import settings
from app.database import async_session_factory
from app.models import Train, Seat, User, Reservation, ReservationStatus
from app.kafka import RESERVATION_TOPIC


# async def get_or_create_user(session: AsyncSession, name: str) -> User:
#     user = await session.scalar(select(User).where(User.name == name))
#     if user:
#         return user
#     user = User(name=name)
#     session.add(user)
#     await session.flush()
#     return user


async def handle_event(session: AsyncSession, event: dict) -> None:
    train = await session.scalar(select(Train).where(Train.code == event["train_code"]))
    if train is None:
        print(f"[worker] 알 수 없는 열차 코드: {event['train_code']}, 무시")
        return
    

    seat = await session.scalar(
        select(Seat).where(Seat.train_id == train.id, Seat.seat_number == event["seat_number"])
    )
    if seat is None:
        print(f"[worker] 알 수 없는 좌석: {event['seat_number']}, 무시")
        return
    

    user = await session.get(User, event["user_id"])
    if user is None:
        print(f"[worker] 알 수 없는 사용자: {event['user_id']}, 무시")
        return


    reservation = Reservation(
        seat_id=seat.id,
        user_id=user.id,
        hold_token=event["hold_token"],
        status=ReservationStatus.HELD,
        held_at=datetime.fromisoformat(event["held_at"]),
        expired_at=datetime.fromisoformat(event["expires_at"]),
    )
    session.add(reservation)

    try:
        await session.commit()

        print(f"[worker] 예약 기록 완료: {event['seat_number']} - {user.name}")

    except IntegrityError:
        # Redis Lua에서 이미 막았어야 정상이지만, DB 레벨 partial unique index가
        # 혹시 모를 상황을 한 번 더 막아주는 이중 방어선 역할
        await session.rollback()
        print(f"[worker] 이미 유효한 예약이 존재하는 좌석 (DB 이중 방어): {event['seat_number']}")

async def main():
    consumer = AIOKafkaConsumer(
        RESERVATION_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="reservation-worker",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        # 이 워커가 처음 실행되는 거라면(저장된 offset이 없으면) 토픽의 맨 처음부터 읽음
        auto_offset_reset="earliest",
    )
    await consumer.start()
    print("[worker] started, listening to reservation-events")

    try:
        async for message in consumer:
            event = message.value
            print(f"[worker] received: {event}")
            async with async_session_factory() as session:
                await handle_event(session, event)
    finally:
        await consumer.stop()
 
 
if __name__ == "__main__":
    asyncio.run(main())