FROM python:3.11-slim

# 실행 위치 설정
WORKDIR /app

# 위치 지정
ENV PYTHONPATH=/app

# 필요한 파일 복사
COPY . .

# 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
