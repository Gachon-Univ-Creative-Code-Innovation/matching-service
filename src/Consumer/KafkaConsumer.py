from kafka import KafkaConsumer
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
import json
import os


from src.Utils.Embedder import Embedding
from src.Consumer.QdrantClient import upsertVector


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BROKER = os.getenv("KAFKA_BROKER")


# Kafka Json Message 형태
class TagMessage(BaseModel):
    userID: str
    tags: List[str]


# Kafka Consumer (Kafka 메세지 소비)
def consume():
    consumer = KafkaConsumer(
        "GithubTags",
        "BlogTags",
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    for message in consumer:
        data = TagMessage(**message.value)
        tagVector = [(tag, Embedding(tag)) for tag in data.tags]
        upsertVector(data.userID, tagVector)
