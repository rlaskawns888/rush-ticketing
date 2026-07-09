from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    redis_url: str

    #스케줄러 1s 대기열에서 꺼내는 인원 수
    admit_batch_size: int = 3

    #입장 토큰 유효 시간(초) - 시간 내 좌석 선택 않으면 토큰 만료 
    admit_ttl_seconds: int = 300

    #kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    #JWT
    jwt_secret_key: str = "dev-secret-change-me-in-production"
    jwt_expire_minutes: int = 1440  # 24시간

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()