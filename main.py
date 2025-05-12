import asyncio
from fastapi import FastAPI
from src.Consumer.FastApiConsumer import KafkaTagConsumer

from src.Service.SearchUser import SearchUsers
from src.Consumer.QdrantClient import InitQdrant
from src.Service.RepresentUser import RepresentTags

app = FastAPI(title="Matching Service")
consumer = KafkaTagConsumer(["GithubTags", "BlogTags"])


# Kafka Consumer 실행
@app.on_event("startup")
async def startup_event():
    await InitQdrant()
    await consumer.start()


# Kafka Consumer 종료
@app.on_event("shutdown")
async def shutdown_event():
    await consumer.stop()


# Tag 기반으로 가장 유사도가 높은 유저 검색
@app.get("/api/matching-service/search-user")
async def search_user(tags: str, topK: int = 5, topKperTag: int = 5):
    try:
        tags = tags.split(",")
        result = await asyncio.to_thread(SearchUsers, tags, topK, topKperTag)
        return {"status": 200, "message": "유저 검색 성공", "data": result}
    except Exception as e:
        return {"status": 500, "message": "유저 검색 실패", "error": str(e)}


# 유저의 대표 태그 검색 API
@app.get("api/matching-service/represent-tags")
async def SearchRepresent(userID: int, topK: int):
    try:
        tags = await asyncio.to_thread(RepresentTags, userID, topK)
        return {"status": 200, "message": "대표 태그 추출 성공", "data": tags}
    except Exception as e:
        return {
            "status": 500,
            "message": "대표 태그 추출 실패",
            "error": str(e),
        }


# 헬스 체크
@app.get("/api/matching-service/health-check")
async def health_check():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
