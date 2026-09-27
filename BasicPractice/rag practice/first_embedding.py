import os

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents="Birth registration requires a hospital letter and parents' citizenship copy."
)

if result.embeddings:
    embedding = result.embeddings[0].values
    if embedding:
        print("Vector length:", len(embedding))
        print("First 5 numbers:", embedding[:50])
    else:
        print("Embedding values are empty.")
else:
    print("No embedding returned.")
