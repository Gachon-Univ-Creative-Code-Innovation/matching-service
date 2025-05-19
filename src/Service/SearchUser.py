import os
from typing import List, Dict
from dotenv import load_dotenv
from urllib.parse import urlparse
from collections import defaultdict
from qdrant_client import QdrantClient


from src.Utils.Embedder import Embedding

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))

QDRANT_HOST = None
QDRANT_PORT = None

rawQdrant = os.getenv("QDRANT_PORT")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

if rawQdrant:
    try:
        parsed = urlparse(rawQdrant)
        if parsed.hostname and parsed.port:
            QDRANT_HOST = parsed.hostname
            QDRANT_PORT = parsed.port
    except Exception:
        pass

if not QDRANT_HOST:
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")

if not QDRANT_PORT:
    QDRANT_PORT = int(os.getenv("QDRANT_PORT_NUM", 6333))


client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# Tag 별로 유저를 검색하여 평균적으로 높은 유저를 찾는 함수
# topK: 검색할 유저의 수, topKperTag: 태그별로 검색할 유저의 수
def SearchUsers(tags: List[str], topK: int = 5, topKperTag: int = 5) -> List[Dict]:
    userScores = defaultdict(list)

    # 여러 태그의 벡터를 한번에 계산하고, None이 아닌 벡터만 필터링
    vectors = [Embedding(tag) for tag in tags]
    vectors = [vector for vector in vectors if vector is not None]  # None 벡터 제외

    # 유효한 벡터가 없다면 빈 리스트 반환
    if not vectors:
        return []

    # 각 태그에 대해 검색 수행
    for i, vector in enumerate(vectors):
        results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=topKperTag,
            with_payload=True,
        )

        for result in results:
            userID = result.payload.get("userID")
            score = result.score
            userScores[userID].append(score)

    # 유저 점수 계산
    avgScores = [
        {
            "userID": userID,
            "score": sum(scores) / len(scores),
            "matched": len(scores),
        }
        for userID, scores in userScores.items()
    ]

    # 점수를 기준으로 내림차순 정렬 후, 상위 topK 유저만 반환
    avgScores.sort(key=lambda x: x["score"], reverse=True)
    return avgScores[:topK]
