import os
import time
import json
import asyncio
import requests
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer


from src.Utils.Embedder import Embedding
from src.Consumer.QdrantClient import UpsertVector


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
LOKI_HOST = os.getenv("LOKI_HOST")


# Kafka Json Message 형태
class TagMessage(BaseModel):
    userID: str
    tags: List[str]


# Loki DB에 태그 정보 저장
async def SaveTagToLoki(userID: str, tag: str):
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
        print(f"Error saving to Loki: {e}")


class KafkaTagConsumer:
    # 인스턴스 초기화
    def __init__(self, topics):
        self.topics = topics
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        self._running = True
        self._task = None

    # Kafka 연결 시작
    async def start(self):
        await self.consumer.start()
        self._task = asyncio.create_task(self.consumeLoop())

    # 메시지 소비
    async def consumeLoop(self):
        try:
            while self._running:
                result = await self.consumer.getmany(timeout_ms=1000)
                for _, messages in result.items():
                    for message in messages:
                        await self.handleMessage(message)
        except Exception as e:
            print(f"[Kafka Consumer Error] {e}")
        finally:
            await self.consumer.stop()

    # 메시지 처리
    async def handleMessage(self, message):
        try:
            data = TagMessage(**message.value)
            tag_vector = [(tag, Embedding(tag)) for tag in data.tags]
            for tag in data.tags:
                await SaveTagToLoki(data.userID, tag)
            await UpsertVector(data.userID, tag_vector)
        except Exception as e:
            print(f"[Message Handling Error] {e}")

    # Consumer 종료
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
