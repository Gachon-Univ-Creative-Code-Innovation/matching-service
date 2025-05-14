import os
import asyncio
import logging
import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

# Logger 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# Cosine Similarity 계산하는 함수
def CosineSim(vec1, vec2):
    v1, v2 = np.array(vec1), np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# 유저의 대표 태그를 topK 개 뽑는 함수
async def RepresentTags(userID: int, topK: int = 5):
    try:
        # Qdrant에서 해당 유저의 모든 태그 벡터 가져오기
        try:
            points, _ = await asyncio.to_thread(
                client.scroll,
                collection_name=QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[FieldCondition(key="userID", match=MatchValue(value=userID))],
                ),
                with_vectors=True,
                with_payload=True,
            )
        except Exception as e:
            logger.error(f"Error while fetching data from Qdrant: {e}")
            return []

        if not points:
            logger.info(f"No points found for userID={userID}")
            return []

        tagVectors = [(point.payload["tag"], point.vector) for point in points]

        # 대표 벡터 (유저) 생성
        vectors = np.array([vec for _, vec in tagVectors])
        RepresentVector = np.mean(vectors, axis=0)

        # 각 태그 벡터와 대표 벡터 간 유사도 계산
        similarities = [
            (tag, CosineSim(RepresentVector, vec)) for tag, vec in tagVectors
        ]

        # 유사도 기준 정렬 후 대표 태그 선택
        RepresentTags = sorted(similarities, key=lambda x: x[1], reverse=True)[:topK]

        return [tag for tag, _ in RepresentTags]

    except Exception as e:
        logger.error(f"Error in RepresentTags: {str(e)}")
        return []
