import os
import json
import asyncio
import logging
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter


from src.Utils.Embedder import Embedding
from src.Consumer.QdrantClient import UpsertVector


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tagCounter = Counter("user_tags_total", "Total number of tags processed", ["tag"])


# Kafka Json Message 형태
class TagMessage(BaseModel):
    userID: int
    tags: List[str]


class KafkaTagConsumer:
    # 인스턴스 초기화
    def __init__(self, topics):
        self.topics = topics
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_deserializer=lambda x: (
                json.loads(x.decode("utf-8")) if x is not None else None
            ),
        )
        self._running = True
        self._task = None

    # Kafka 연결 시작
    async def Start(self):
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                await self.consumer.start()
                self._task = asyncio.create_task(self.ConsumeLoop())
                logger.info("✅ Kafka consumer started successfully.")
                return
            except Exception as e:
                logger.error(
                    f"❌ Kafka start failed (attempt {attempt}/{max_retries}): {e}"
                )
                await asyncio.sleep(5)

        raise ConnectionError("Kafka consumer could not connect after retries.")

    # 메시지 소비
    async def ConsumeLoop(self):
        try:
            while self._running:
                result = await self.consumer.getmany(timeout_ms=1000)
                for topic_partition, messages in result.items():
                    if messages:
                        logger.info(
                            f"Received {len(messages)} messages from {topic_partition}"
                        )
                    for message in messages:
                        try:
                            await self.HandleMessage(message)
                        except Exception as e:
                            logging.error(
                                f"Error handling message: {e}"
                            )  # 개별 메시지 처리 실패 시 로깅
        except Exception as e:
            logger.error(f"[Kafka Consumer Error] {e}")
        finally:
            await self.consumer.stop()

    # 메시지 처리
    async def HandleMessage(self, message):
        try:
            data = message.value
            if data is None:
                logger.warning(f"[Kafka] Received None data. Raw message: {message}")
                return
            payload = data.get("payload", {})
            op = payload.get("op")  # c (create), u (update), d (delete) 등

            # create만 구독, 나머지는 무시
            if op != "c":
                logger.info(f"[Kafka] Non-create op ignored. op={op}, message: {data}")
                return

            after = payload.get("after", {})
            if not after:
                logger.warning(f"[Kafka] after is empty. Raw message: {message.value}")
                return

            userID = after.get("user_id")
            tag = after.get("tag_name")
            if userID is None or tag is None:
                logger.warning(
                    f"[Kafka] user_id or tag_name missing. after: {after}, topic: {message.topic}"
                )
                return

            # 벡터 생성 및 저장
            vector = Embedding(tag)
            logging.info(
                f"[Kafka] topic={message.topic}, op={op}, tag={tag}, user_id={userID}, vector={vector}"
            )

            tagCounter.labels(tag=tag).inc()
            await UpsertVector(int(userID), [(tag, vector)])

        except Exception as e:
            logger.error(
                f"[Message Handling Error] {e}, message: {getattr(message, 'value', None)}"
            )
            import traceback

            logger.error(traceback.format_exc())

    # Consumer 종료
    async def Stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logging.info("Consumer task cancelled.")
