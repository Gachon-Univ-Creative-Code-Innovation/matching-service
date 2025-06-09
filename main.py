import asyncio
import logging
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from src.Consumer.FastApiConsumer import KafkaTagConsumer
from src.Service.SearchUser import SearchUsers
from src.Consumer.QdrantClient import InitQdrant
from src.Service.RepresentUser import RepresentTags
from src.Utils.GetJWT import GetTokenFromHeader, GetDataFromToken

app = FastAPI(title="Matching Service")


consumer = KafkaTagConsumer(topics=["server.public.Career_Tag", "server.public.tag"])
instrumentator = Instrumentator().instrument(app).expose(app)


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Kafka Consumer 실행
@app.on_event("startup")
async def StartupEvent():
    logger.info("Starting Qdrant initialization...")
    await InitQdrant()

    logger.info("Starting Kafka consumer...")
    await consumer.Start()


# Kafka Consumer 종료
@app.on_event("shutdown")
async def ShutdownEvent():
    await consumer.Stop()


# Tag 기반으로 가장 유사도가 높은 유저 검색
@app.get("/api/matching-service/search-user")
async def SearchUser(request: Request, tags: str, topK: int = 5, topKperTag: int = 10):
    try:
        accessToken = GetTokenFromHeader(request)
        userID = GetDataFromToken(accessToken, "user_id")
        tags = [tag.strip().lstrip("#").strip() for tag in tags.split(",")]
        result = await asyncio.to_thread(SearchUsers, tags, userID, topK, topKperTag)
        return {"status": 200, "message": "유저 검색 성공", "data": result}
    except Exception as e:
        return {"status": 500, "message": "유저 검색 실패", "error": str(e)}


# 유저의 대표 태그 검색 API
@app.get("/api/matching-service/represent-tags")
async def SearchRepresent(userID: int, topK: int):
    try:
        tags = await RepresentTags(userID, topK)
        return {"status": 200, "message": "대표 태그 추출 성공", "data": tags}
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
