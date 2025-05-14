import os
import logging
import numpy as np
from google import genai
from dotenv import load_dotenv

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# Normalization
def Normalize(vector):
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector  # 제로 벡터는 그대로 반환 (정규화 불가능)
    return (vector / norm).tolist()


# Emvedding function
def Embedding(tag: str):
    try:
        vector = (
            client.models.embed_content(model="models/text-embedding-004", contents=tag)
            .embeddings[0]
            .values
        )

        embedding = Normalize(vector)
        return embedding

    except Exception as e:
        logging.error(f"Gemini API exception: {e}")
        return None
