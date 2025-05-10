import os
from typing import List, Dict
from collections import defaultdict
from dotenv import load_dotenv
from qdrant_client import QdrantClient

from src.Utils.Embedder import Embedding

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")


client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


# Tag 별로 유저를 검색하여 평균적으로 높은 유저를 찾는 함수
# topK: 검색할 유저의 수, topKperTag: 태그별로 검색할 유저의 수
def SearchUsers(tags: List[str], topK: int = 5, topKperTag: int = 5) -> List[Dict]:
    userScores = defaultdict(list)

    for tag in tags:
        vector = Embedding(tag)
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

    avgScores = [
        {
            "userID": userID,
            "score": sum(scores) / len(scores),
            "matched": len(scores),
        }
        for userID, scores in userScores.items()
    ]

    avgScores.sort(key=lambda x: x["score"], reverse=True)
    return avgScores[:topK]
