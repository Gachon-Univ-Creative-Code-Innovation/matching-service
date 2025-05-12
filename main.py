from fastapi import FastAPI
import threading

from src.Consumer.KafkaConsumer import Consume
from src.Consumer.QdrantClient import InitQdrant
from src.Service.SearchUser import SearchUsers
from src.Service.RepresentUser import RepresentTags

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


# 유저의 대표 태그 검색 API
async def SearchRepresent(userID: int, topK: int):
    try:
        tags = RepresentTags(userID, topK)
        return {"status": 200, "meassage": "대표 태그 추출 성공", "data": tags}
    except Exception as e:
        return {
            "status": 500,
            "message": "대표 태그 추출 실패",
            "error": str(e),
        }


# 헬스 체크
@app.get("/api/matching-service/health-check")
async def HealthCheck():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
