from kafka import KafkaConsumer
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
import requests
import time
import json
import os


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
def SaveTagToLoki(userID: str, tag: str):
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
        requests.post(f"{LOKI_HOST}/loki/api/v1/push", json=logEntry)
    except Exception as e:
        print(f"Error saving to Loki: {e}")


# Kafka Consumer (Kafka 메세지 소비)
def Consume():
    consumer = KafkaConsumer(
        "GithubTags",
        "BlogTags",
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    for message in consumer:
        data = TagMessage(**message.value)
        tagVector = [(tag, Embedding(tag)) for tag in data.tags]

        # Loki에 각 태그 로그 저장
        for tag in data.tags:
            SaveTagToLoki(data.userID, tag)

        UpsertVector(data.userID, tagVector)
