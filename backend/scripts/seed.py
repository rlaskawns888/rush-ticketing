import asyncio
from datetime import datetime, timedelta, timezone
 
from sqlalchemy import select
 
from app.database import async_session_factory
from app.models import Train, Seat
 

TRAIN_CODE = "train-001"
ROWS = 6 #1-6행
COLUMNS = ["A", "B", "C", "D"] #A,D=창측 / B,C=내측 (실제 KTX 표기 방식)
SEAT_COUNT = ROWS * len(COLUMNS)


async def seed():
    async with async_session_factory() as session:
        #중복 생성 방지
        existing = await session.scalar(select(Train).where(Train.code == TRAIN_CODE))
        
        if existing:
            print(f"이미 존재하는 열차입니다: {TRAIN_CODE} (id={existing.id})")
            return
        
        train = Train(
            code=TRAIN_CODE,
            name="KTX-101",
            departure_at=datetime.now(timezone.utc) + timedelta(days=1),
            total_seats=SEAT_COUNT,
        )
        session.add(train)
        await session.flush() # train.id를 미리 받아오기 위해 flush (commit 전 DB에 반영)

        for row in range(1, ROWS + 1):
            for col in COLUMNS:
                seat = Seat(train_id=train.id, seat_number=f"{row}{col}")
                session.add(seat)

        await session.commit()
        print(f"생성 완료: {TRAIN_CODE} (id={train.id}), 좌석 {SEAT_COUNT}개 (1A~{ROWS}D)")
 
 
if __name__ == "__main__":
    asyncio.run(seed())
