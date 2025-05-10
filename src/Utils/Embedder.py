from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("Leejy0-0/kr-con-embedding-sbert-v2")


# Normalization
def Normalize(vector):
    norm = (vector / np.linalg.norm(vector)).tolist()
    return norm


# Emvedding function
def Embedding(tag: str):

    vector = model.encode(tag)
    embedding = Normalize(vector)
    return embedding
