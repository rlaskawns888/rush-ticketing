from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db_session, get_redis
from app.routes import queue

app = FastAPI(title="rush-ticketing")
app.include_router(queue.router) 

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