from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.auth import get_current_user
from app.database import get_db_session
from app.models import User, Reservation, ReservationStatus, Seat, Train


router = APIRouter(
    prefix="/users", 
    tags=["users"]
)


@router.get("/me/reservation")
async def get_my_reservation(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
        로그인한 사용자의 현재 유효한(HELD/CONFIRMED) 예약을 조회.
        hold_token을 DB에서 바로 꺼내주므로, 새로고침하거나 다른 기기에서 로그인해도
        화면 상태(React state)에 의존하지 않고 예약을 다시 찾을 수 있음.
    """
    reservation = await session.scalar(
        select(Reservation).where(
            Reservation.user_id == current_user.id,
            Reservation.status.in_([ReservationStatus.HELD, ReservationStatus.CONFIRMED]),
        )
    )
 
    if reservation is None:
        return {"has_reservation": False}
 
    seat = await session.get(Seat, reservation.seat_id)
    train = await session.get(Train, seat.train_id)
 
    return {
        "has_reservation": True,
        "status": reservation.status.value,
        "train_id": train.code,
        "train_name": train.name,
        "seat_number": seat.seat_number,
        "hold_token": reservation.hold_token,
    }