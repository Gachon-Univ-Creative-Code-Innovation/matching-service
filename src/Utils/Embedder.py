from sentence_transformers import SentenceTransformer
import numpy as np


# Normalization
def Normalize(vector):
    norm = (vector / np.linalg.norm(vector)).tolist()
    return norm


# Emvedding function
def Embedding(tag: str):
    model = SentenceTransformer("all-mpnet-base-v2")
    vector = model.encode(tag)
    embedding = Normalize(vector)
    return embedding
