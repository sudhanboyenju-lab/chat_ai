import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(model="gemini-3.6-flash")

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