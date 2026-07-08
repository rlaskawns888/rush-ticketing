from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db_session, get_redis
from app.routes import queue, reservation, auth, users
from app.kafka import start_producer, stop_producer


@asynccontextmanager
async def lifesapn(app: FastAPI):
    await start_producer() #앱 시작 시 호출
    yield #try, catch 라고 생각하면 됨ㄴ
    await stop_producer() #앱 종료 시 호출 


app = FastAPI(title="rush-ticketing", lifespan=lifesapn)

# React 개발 서버(5173번 포트)에서의 요청을 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(queue.router) 
app.include_router(reservation.router) 
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    """가장 기본적인 살아있는지 체크 (DB/Redis 연결 여부와 무관)"""
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db_session)):
    """Postgres 연결이 실제로 되는지 확인"""
    result = await session.execute(text("SELECT 1"))
    return {"status": "ok", "result": result.scalar()}


@app.get("/health/redis")
async def health_redis(redis: Redis = Depends(get_redis)):
    """Redis 연결이 실제로 되는지 확인"""
    pong = await redis.ping()
    return {"status": "ok", "pong": pong}