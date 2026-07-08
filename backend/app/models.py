import enum
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Integer, Enum, UniqueConstraint, Index, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class ReservationStatus(str, enum.Enum):
    HELD = "HELD"           #좌석 선점, 결제 대기(TTL 있음)
    CONFIRMED = "CONFIRMED" #예약 확정
    EXPIRED = "EXPIRED"     #제한 시간 초과로 자동 만료 
    CANCELLED = "CANCELLED" #취소


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True)  # 예: "train-001" (Redis 키, URL 등에서 사용)
    name: Mapped[str] = mapped_column(String(100)) #KTX
    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_seats: Mapped[int] = mapped_column(Integer)

    seats: Mapped[list["Seat"]] = relationship(back_populates="train")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        #같은 열차 안에서 좌석 번호 중복될 수 없음
        UniqueConstraint("train_id", "seat_number", name="uq_train_seat_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    train_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trains.id"))
    seat_number: Mapped[str] = mapped_column(String(10)) #ex) A1, A2

    train: Mapped["Train"] = relationship(back_populates="seats")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="seat")


class User(Base):
    __tablename__ = "users"
 
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)  # 로그인 아이디
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(50))


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        # 좌석당 HELD/CONFIRMED 상태인 예약은 동시에 1건만 존재 
        # (partial unique index로 DB 레벨 이중 방어)
        Index (
            "uq_seat_active_reservation",
            "seat_id",
            unique=True,
            postgresql_where = text("status IN ('HELD', 'CONFIRMED')"),
        ),
    )
    """
        partial unique index? 

        1. 사용자1이 예약했다가 취소(CANCELLED) → 기록 남음
        2. 사용자2가 다시 예약해서 확정(CONFIRMED) → 기록 남음
        3. seat_id는 A1로 동일
        : 일반 Unique 제약이였다면, 위에 상황에서 에러가 발생했을것임 

        - 같은 좌석에 동시에 유효한(HELD/CONFIRMED) 예약이 2개 이상 존재하는것으로
        유니크 검사 대상으로 만든것임
    """

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seats.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    hold_token: Mapped[str] = mapped_column(String(64))  # 로그인만으로 예약을 다시 찾을 수 있게 DB에도 저장
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        default=ReservationStatus.HELD,
    )
    held_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    seat: Mapped["Seat"] = relationship(back_populates="reservations")
