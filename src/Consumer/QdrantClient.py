import os
import asyncio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# Qdrant Client 초기화
async def InitQdrant():
    response = await asyncio.to_thread(client.get_collections)
    collections = [c.name for c in response.collections]

    if QDRANT_COLLECTION not in collections:
        await asyncio.to_thread(
            client.create_collection,
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    else:
        print(f"컬렉션 '{QDRANT_COLLECTION}'이 이미 존재합니다.")


# Qdrant Vector 저장 (덮어쓰기)
async def UpsertVector(userID, tagVect: list):
    points = [
        PointStruct(
            id=f"{userID}_{tag}", vector=vector, payload={"userID": userID, "tag": tag}
        )
        for tag, vector in tagVect
    ]

    # 배치 크기 조정 (여기서는 100개로 설정)
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        await asyncio.to_thread(
            client.upsert, collection_name=QDRANT_COLLECTION, points=batch
        )
        print(f"업로드된 벡터 개수: {len(batch)}")
