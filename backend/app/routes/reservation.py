import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
 
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.database import get_redis, get_db_session
from app.redis_keys import admit_key
from app.kafka import publish_reservation_event
from app.models import Train, Seat, Reservation, ReservationStatus, User
from app.auth import get_current_user

router = APIRouter(
    prefix="/trains",
    tags=["reservation"]    
)

HOLD_TTL_SECONDS = 180
# HOLD_TTL_SECONDS = 30

# Lua 스크립트 파일 읽어 문자열로 보관 
_LUA_PATH = Path(__file__).parent.parent / "lua" / "hold_seat.lua"
HOLD_SEAT_SCRIPT = _LUA_PATH.read_text(encoding="utf-8")


def seat_hold_key(train_id: str, seat_number: str) -> str:
    return f"hold:{train_id}:{seat_number}"


class ConfirmSeatRequest(BaseModel):
    hold_token: str


class CancelSeatRequest(BaseModel):
    hold_token: str


@router.get("/{train_id}/seats")
async def list_seats(
    train_id: str, 
    redis: Redis = Depends(get_redis), 
    session: AsyncSession = Depends(get_db_session)
):
    """
        좌석 배치도 조회
        - 각 좌석의 행/열과 현재 선점 여부를 같이 내려줌
        - Redis에 hold키가 있으면 (TTL 살아있는 동안) 선점 중 or 이미 확정된 좌석 
    """
    train = await session.scalar(select(Train).where(Train.code == train_id))
    if train is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 열차입니다.")
    
    seats = (await session.scalars(select(Seat).where(Seat.train_id == train.id))).all()

    result = []
    for seat in seats:
        is_taken = await redis.exists(seat_hold_key(train_id, seat.seat_number))

        result.append(
            {
                "seat_number": seat.seat_number,
                "row": int(seat.seat_number[:-1]),
                "column": seat.seat_number[-1],
                "is_available": not bool(is_taken),
            }
        )
    
    return {"train_name": train.name, "seats": result}


@router.post("/{train_id}/seats/{seat_number}/hold")
async def hold_seat(
    train_id: str,
    seat_number: str,
    x_admit_token: str = Header(..., validation_alias="X-Admit-Token"),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db_session)    
):
    """ 좌석 선점 """

    #입장 토큰 검증 
    admitted = await redis.get(admit_key(x_admit_token))
    if not admitted:
        raise HTTPException(
            status_code=403, 
            detail="입장 토큰이 유효하지 않습니다."
        )


    #예약 1건만 가능
    existing = await session.scalar(
        select(Reservation).where(
            Reservation.user_id == current_user.id,
            Reservation.status.in_([ReservationStatus.HELD, ReservationStatus.CONFIRMED]),
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="이미 진행 중인 예약이 있어요. 예약확인에서 확인해주세요.",
        )


    #Lua 스크립트 원자적 좌석 선점 시도
    hold_token = str(uuid.uuid4()) #선점 건의 소유자 식별 (나중 결제 확정에 사용)

    result = await redis.eval(
        HOLD_SEAT_SCRIPT,
        1,
        seat_hold_key(train_id, seat_number),   #KEY[1]
        hold_token,                             #ARGV[1]
        HOLD_TTL_SECONDS                        #ARGV[2]
    )

    if result == 0:
        raise HTTPException(status_code=409, detail="이미 다른 사용자가 선점한 좌석입니다.")
    

    #Redis 선점 성공 -> Kafka에 이벤트 발행 (DB 기록은 worker가 비동기로 처리)
    now = datetime.now(timezone.utc)
    event = {
        "train_code": train_id,
        "seat_number": seat_number,
        "hold_token": hold_token,
        "user_id": str(current_user.id),
        "held_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=HOLD_TTL_SECONDS)).isoformat(),
    }
    await publish_reservation_event(event)
    
    return {
        "seat_number": seat_number,
        "hold_token": hold_token,
        "expires_in_seconds": HOLD_TTL_SECONDS,
    }


@router.post("/{train_id}/seats/{seat_number}/confirm")
async def confirm_seat(
    train_id: str,
    seat_number: str,
    body: ConfirmSeatRequest,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db_session),
):
    """
        결제 완료(예시) 후 호출. HELD 상태의 예약을 CONFIRMED로 확정.
    
        1. Redis에 저장된 hold_token과 요청으로 온 hold_token이 일치하는지 확인
        (이걸 확인 안 하면, 다른 사람이 hold_token만 알아내서 남의 예약을 확정시킬 수 있음)

        2. Redis 키의 TTL을 없애서(PERSIST) 영구 선점 상태로 전환
        (그냥 두면 3분 뒤 만료돼서, 결제까지 끝난 좌석이 다시 풀려버림)

        3. Postgres의 예약 상태를 HELD -> CONFIRMED로 변경
    """
    key = seat_hold_key(train_id, seat_number)
    current_hold_token = await redis.get(key)

    if current_hold_token != body.hold_token:
        raise HTTPException(status_code=403, detail="유효하지 않은 예약 정보입니다.")
    
    await redis.persist(key) #TTL제거 -> 자동 만료 X

    train = await session.scalar(select(Train).where(Train.code == train_id))

    seat = await session.scalar(
        select(Seat).where(Seat.train_id == train.id, Seat.seat_number == seat_number)
    )

    #worker가 Kafka 이벤트 치러 중일 수 있어서, 짧게 재시도하며 기다림 
    reservation = None
    for _ in range(5):       
        reservation = await session.scalar(
            select(Reservation).where(
                Reservation.seat_id == seat.id,
                Reservation.status == ReservationStatus.HELD,
                Reservation.user_id == current_user.id,  # 본인 예약인지 확인
            )
        )
        if reservation is not None:
            break
        await asyncio.sleep(0.3)
    
    if reservation is None:
        raise HTTPException(
            status_code=409,
            detail="본인 명의의 예약 정보를 찾을 수 없어요. 잠시 후 다시 시도해주세요.",
        )
    
    reservation.status = ReservationStatus.CONFIRMED
    reservation.confirmed_at = datetime.now(timezone.utc)
    await session.commit()

    return {
        "seat_number": seat_number,
        "train_name": train.name,
        "status": "CONFIRMED",
        "confirmed_at": reservation.confirmed_at.isoformat(),
    }


@router.post("/{train_id}/seats/{seat_number}/cancel")
async def cancel_seat(
    train_id: str,
    seat_number: str,
    body: CancelSeatRequest,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_db_session),
):
    """
    예약 취소. 결제 전(HELD) 상태에서 "다른 좌석 고르기"로 되돌아갈 때도,
    결제 후(CONFIRMED) 상태에서 정식으로 예약을 취소할 때도 같은 API를 씀.
 
    1. hold_token 일치 확인 (남의 예약을 취소하는 것 방지)
    2. Redis 키를 완전히 삭제 -> 좌석이 즉시 다시 선택 가능해짐
       (confirm에서 PERSIST로 TTL을 없앴어도, DEL은 TTL 여부와 무관하게 바로 지워짐)
    3. DB 예약 상태를 CANCELLED로 변경
    """
    key = seat_hold_key(train_id, seat_number)
    current_hold_token = await redis.get(key)
 
    if current_hold_token != body.hold_token:
        raise HTTPException(status_code=403, detail="유효하지 않은 예약 정보입니다.")
 
    await redis.delete(key)  # 좌석 즉시 반납
 
    train = await session.scalar(select(Train).where(Train.code == train_id))
    seat = await session.scalar(
        select(Seat).where(Seat.train_id == train.id, Seat.seat_number == seat_number)
    )
 
    reservation = await session.scalar(
        select(Reservation).where(
            Reservation.seat_id == seat.id,
            Reservation.status.in_([ReservationStatus.HELD, ReservationStatus.CONFIRMED]),
            Reservation.user_id == current_user.id,  # 본인 예약인지 확인
        )
    )
 
    if reservation is not None:
        reservation.status = ReservationStatus.CANCELLED
        await session.commit()
 
    return {"seat_number": seat_number, "status": "CANCELLED"}