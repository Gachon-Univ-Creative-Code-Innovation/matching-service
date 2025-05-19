import os
import time
import json
import asyncio
import requests
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer
import logging

from src.Utils.Embedder import Embedding
from src.Consumer.QdrantClient import UpsertVector


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
LOKI_HOST = os.getenv("LOKI_HOST")

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Kafka Json Message 형태
class TagMessage(BaseModel):
    userID: int
    tags: List[str]


# Loki DB에 태그 정보 저장
async def SaveTagToLoki(userID: int, tag: str):
    logLIne = f"userID={userID} tags={tag}"
    timestamp = int(time.time() * 1e9)

    logEntry = {
        "streams": [
            {
                "stream": {"job": "tag-consumer", "tag": tag},
                "values": [[str(timestamp), logLIne]],
            }
        ]
    }

    try:
        await asyncio.to_thread(
            requests.post, f"{LOKI_HOST}/loki/api/v1/push", json=logEntry
        )
    except Exception as e:
        logger.error(f"Error saving to Loki: {e}")


class KafkaTagConsumer:
    # 인스턴스 초기화
    def __init__(self, topics):
        self.topics = topics
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        self._running = True
        self._task = None

    # Kafka 시작할 때까지 기다림
    async def WaitKafka(self, host="kafka", port=9092, timeout=30):
        for _ in range(timeout):
            try:
                _, self.writer = await asyncio.open_connection(host, port)
                self.writer.close()
                await self.writer.wait_closed()
                return True
            except Exception as e:
                logger.error(f"Error connecting to Kafka: {e}")
                await asyncio.sleep(1)
        raise ConnectionError(
            f"Kafka at {host}:{port} is not available after {timeout} seconds."
        )

    # Kafka 연결 시작
    async def Start(self):
        await self.consumer.start()
        self._task = asyncio.create_task(self.ConsumeLoop())

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
            payload = data.get("payload", {})
            op = payload.get("op")  # c (create), u (update), d (delete) 등

            if op not in ("c", "u"):
                return

            after = payload.get("after", {})
            if not after:
                return

            userID = str(after["user_id"])
            tag = after["tag_name"]

            # 벡터 생성 및 저장
            vector = Embedding(tag)
            logging.info(f"[Kafka] op={op}, tag={tag}, vector={vector}")

            # Loki 저장
            await SaveTagToLoki(userID, tag)
            await UpsertVector(int(userID), [(tag, vector)])

        except Exception as e:
            logger.error(f"[Message Handling Error] {e}")

    # Consumer 종료
    async def Stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logging.info("Consumer task cancelled.")
