import os

from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads the .env file and loads variables into memory

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# input = input("You: ")

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="In one sentence, explain what RAG is."
)

print(response.text)