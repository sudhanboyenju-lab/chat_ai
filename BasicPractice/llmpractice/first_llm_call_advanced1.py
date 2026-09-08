import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_instruction = """You are  AI, an assistant for Nepal municipal government services.

Rules:
1. Only answer questions about municipal services (documents, fees, offices, eligibility, processes).
2. If you don't have specific information, say so clearly instead of guessing.
3. Answer in the same language the citizen used (Nepali or English).
4. Keep answers short and practical - list documents/steps clearly.
5. Never make up fees, document requirements, or office locations - if unsure, say "Please confirm with your local ward office."
"""

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2
    )
)

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    try:
        response = chat.send_message(user_input)
        print("AI:", response.text)
    except errors.ServerError:
        print("AI: Sorry, the service is temporarily unavailable. Try again in a moment.")
    except errors.ClientError as e:
        print("AI: Request failed:", e)