from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from dotenv import load_dotenv
import os

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# Qdrant Client 초기화
def InitQdrant():
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE,
            ),
        )
    else:
        print(f"컬렉션 '{QDRANT_COLLECTION}'이 이미 존재합니다.")


# Qdrant Vector 저장 (덮어쓰기)
def UpsertVector(userID, tagVect: list):
    points = []
    for tag, vector in tagVect:
        pointID = f"{userID}_{tag}"
        points.append(
            PointStruct(
                id=pointID, vector=vector, payload={"userID": userID, "tag": tag}
            )
        )
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
