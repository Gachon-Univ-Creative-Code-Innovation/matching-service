from fastapi import FastAPI
import threading

from src.Consumer.KafkaConsumer import consume
from src.Consumer.QdrantClient import InitQdrant

app = FastAPI(title="Matching Service")


# FastAPI 서버 시작 시 Qdrant 초기화 및 Kafka Consumer 시작
@app.on_event("startup")
def startupEvent():
    InitQdrant()
    threading.Thread(target=consume, daemon=True).start()


# 헬스 체크
@app.get("/api/matching-service/health-check")
async def HealthCheck():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
