from fastapi import FastAPI
import threading

from src.Consumer.KafkaConsumer import Consume
from src.Consumer.QdrantClient import InitQdrant
from src.Service.SearchUser import SearchUsers

app = FastAPI(title="Matching Service")


# FastAPI 서버 시작 시 Qdrant 초기화 및 Kafka Consumer 시작
@app.on_event("startup")
def StartupEvent():
    InitQdrant()
    threading.Thread(target=Consume, daemon=True).start()


# 유저 검색 API
@app.get("/api/matching-service/search-user")
async def SearchUser(tags: str, topK: int = 5, topKperTag: int = 5):
    try:
        tags = tags.split(",")
        result = SearchUsers(tags, topK, topKperTag)
        return {
            "status": 200,
            "message": "유저 검색 성공",
            "data": result,
        }
    except Exception as e:
        return {
            "status": 500,
            "message": "유저 검색 실패",
            "error": str(e),
        }


# 헬스 체크
@app.get("/api/matching-service/health-check")
async def HealthCheck():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
