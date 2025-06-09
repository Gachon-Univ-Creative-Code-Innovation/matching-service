import jwt
import logging
import base64
import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv

app = FastAPI()


# Token에서 필요한 정보 받아내는 코드
# getWhat -> 'sub' = 이메일, 'user_id' = 유저 ID, 'role' = USER/HEAD_HUNTER
def GetDataFromToken(token, getWhat):
    envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(envPath))

    secretKey = os.getenv("JWT_SECRET")
    try:
        decodedSecret = base64.b64decode(secretKey)
        payload = jwt.decode(token, decodedSecret, algorithms=["HS512"])
        return payload[getWhat]
    except Exception as e:
        logging.error(f"[GetDataFromToken] 예외 발생: {e}")
        return None


# 요청 Header에서 Access Token 추출 코드
def GetTokenFromHeader(request: Request):
    header = request.headers.get("Authorization")

    if not header:
        raise ValueError("Authorization 헤더가 없습니다.")
    if not header.startswith("Bearer "):
        raise ValueError("Authorization 헤더가 Bearer 타입이 아닙니다.")

    token = header[len("Bearer ") :]
    if not token:
        raise ValueError("Bearer 토큰이 비어 있습니다.")
    return token
