from google import genai
import numpy as np
import os
from dotenv import load_dotenv


envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# Normalization
def Normalize(vector):
    norm = (vector / np.linalg.norm(vector)).tolist()
    return norm


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
        print(f"Gemini exception: {e}")
