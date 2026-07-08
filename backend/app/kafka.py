import json

from aiokafka import AIOKafkaProducer

from app.config import settings

RESERVATION_TOPIC = "reservation-events"

#앱 시작 시 한번만 생성해서 재사용 (싱글톤) - 커넥션 재사용 목적 
producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")    
    )
    await producer.start()


async def stop_producer() -> None:
    if producer is not None:
        await producer.stop()


async def publish_reservation_event(event: dict) -> None:
    """
        좌석 선점 성공 시 호출 
        send_and_wait: 발행이 실제로 브로커에 반영될 때까지 기다림
        (fire-and-forget인 send()도 있지만, 학습 단계에선 확실하게 확인하고 넘어가는 게 좋음)
    """
    if producer is None:
        raise RuntimeError("Kafka producer가 아직 시작되지 않았습니다.")
    
    await producer.send_and_wait(RESERVATION_TOPIC, event)
 