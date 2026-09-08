import os

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client.models.embed_content(model="gemini-embedding-001", contents=text)
    return result.embeddings[0].values

def cosine_similarity(vec1, vec2):
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Step 1: Multiple documents, not just one
documents = [
    "Birth Registration: requires hospital birth letter, citizenship copy of parents. No fee within 35 days.",
    "Map Approval: requires land ownership certificate, citizenship copy, engineer-approved design. Apply at Ward Office.",
    "Tax Payment: property tax must be paid annually at the Revenue Office. Late payment adds 5% penalty."
]

# Step 2: Embed all documents ONCE, ahead of time
document_embeddings = [get_embedding(doc) for doc in documents]

# # Step 3: Citizen's question
# question = "How do I pay my property tax?"
# question_embedding = get_embedding(question)

# # Step 4: Compare question against EVERY document, find the best match
# scores = [cosine_similarity(question_embedding, doc_emb) for doc_emb in document_embeddings]

# best_index = np.argmax(scores)  # index of the HIGHEST score
# best_document = documents[best_index]

# print("Scores:", scores)
# print("Best matching document:", best_document)

# # Step 5: NOW do the augmentation + generation, using the automatically retrieved doc
# prompt = f"""Answer the question using ONLY the information below.

# Information:
# {best_document}

# Question: {question}
# """

# response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
# print("\nAnswer:", response.text)


test_questions = [
    "What documents do I need for a birth certificate?",
    "How do I get my map approved?",
    "When is property tax due?"
]

for q in test_questions:
    q_embedding = get_embedding(q)
    scores = [cosine_similarity(q_embedding, doc_emb) for doc_emb in document_embeddings]
    best_index = np.argmax(scores)
    print(f"Q: {q}")
    print(f"-> Matched: {documents[best_index]}\n")