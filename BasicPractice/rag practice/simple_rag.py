import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Step 1: Your "knowledge" - just a plain string for now, no database
knowledge = """
Birth Registration Service:
Documents required: hospital birth letter, citizenship copy of both parents, ward recommendation letter.
No fee if registered within 35 days. After 35 days, fee is Rs. 100.
Available at Ward Office, Sunday to Friday, 10 AM to 5 PM.
"""

# Step 2: Citizen's question
# question = "What documents do I need to register a birth?"
# question = "How do I get a map approval?"
question = input("You: ")

# Step 3: Combine knowledge + question into ONE prompt (this IS the "augmentation" in RAG)
prompt = f"""Answer the question using ONLY the information below. If the answer isn't in the information, say you don't know.

Information:
{knowledge}

Question: {question}
"""

# Step 4: Send to the LLM - same generate_content call you already know
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)

print(response.text)