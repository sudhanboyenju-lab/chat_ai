import os

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    if result.embeddings:
        return result.embeddings[0].values
    return None

def cosine_similarity(vec1, vec2):
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Two related sentences
text1 = "I absolutely love this new policy, it has made everyone's life better."
text2 = "What documents do I need to register my newborn's birth?"

# One unrelated sentence
text3 = "The weather in Kathmandu today is sunny."

text_b = "I absolutely hate this new policy, it has ruined everyone's life."
text_c = "I absolutely love this new policy, it has made everyone's life better."
text_d = "I absolutely hate this new policy, it has ruined everyone's life."

embedding1 = get_embedding(text1)
embedding2 = get_embedding(text2)
embedding3 = get_embedding(text3)
embeddingb = get_embedding(text_b)
embeddingc = get_embedding(text_c)
embeddingd = get_embedding(text_d)

if embedding1 and embedding2 and embedding3 and embeddingb and embeddingc and embeddingd:
    similarity_related = cosine_similarity(embedding1, embedding2)
    similarity_unrelated = cosine_similarity(embedding1, embedding3)
    similarity_unrelatedb = cosine_similarity(embedding1, embeddingb)
    similarity_unrelatedc = cosine_similarity(embedding1, embeddingc)
    similarity_unrelatedd = cosine_similarity(embedding1, embeddingd)

    print("Similarity (related texts):", similarity_related)
    print("Similarity (unrelated texts):", similarity_unrelated)
    print("Similarity (unrelated textsb):", similarity_unrelatedb)
    print("Similarity (unrelated textsc):", similarity_unrelatedc)
    print("Similarity (unrelated textsd):", similarity_unrelatedd)