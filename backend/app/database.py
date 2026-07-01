from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import Redis, from_url

from app.config import settings

#PostgreSQL
engine = create_async_engine(settings.database_url, echo=True) # 개발: echo=True SQL 콘솔에 찍힘 
async_session_factory = async_sessionmaker(engine, expire_on_commit=False) #요청 마다 DB 세션 신규 생성 

async def get_db_session() -> AsyncSession:
    """
    FastAPI 라우터에서 Depends(get_db_session)로 주입받아 쓰는 세션.
    Spring의 @Autowired로 Repository 주입받는 것과 비슷한 역할이라고 보면 됨.
    """
    async with async_session_factory() as session:
        yield session

#Redis
redis_client: Redis = from_url(settings.redis_url, decode_responses=True) #커넥션 풀 하나만 만들어서 앱 전체 재사용 

async def get_redis() -> Redis:
    return redis_client