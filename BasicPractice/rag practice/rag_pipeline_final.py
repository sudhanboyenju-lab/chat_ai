from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

text = """Birth Registration Service

To register a child's birth, the following documents are required:
1. Hospital birth letter or health post certificate
2. Citizenship certificate copy of both parents
3. Marriage registration certificate (if applicable)
4. Ward recommendation letter

The service is available at the Ward Office. Registration must be completed within 35 days of birth. There is no fee for registration within this period. After 35 days, a late registration fee of Rs. 100 applies.

Office hours: Sunday to Friday, 10 AM to 5 PM."""
print(text)

# Step 1: Split
splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
chunks = splitter.split_text(text)
documents = [Document(page_content=chunk) for chunk in chunks]
print(documents)

# Step 2: Embed + store
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(documents, embeddings, persist_directory="./chroma_db")

# Step 3: Set up the LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)

# def ask(question):
#     # Retrieval
#     results = vectorstore.similarity_search(question, k=3)
#     retrieved_text = "\n\n".join([doc.page_content for doc in results])

#     # Augmentation
#     prompt = f"""Answer the question using ONLY the information below. If the answer isn't in the information, say you don't know.

#     Information:
#     {retrieved_text}

#     Question: {question}
#     """

#     # Generation
#     response = llm.invoke(prompt)
#     return get_text(response), results

def ask(question, threshold=0.8):
    results_with_scores = vectorstore.similarity_search_with_score(question, k=3)

    # Filter out chunks that are too dissimilar (distance too high)
    relevant_results = [(doc, score) for doc, score in results_with_scores if score < threshold]

    if not relevant_results:
        return "यो सेवाको बारेमा हामीसँग जानकारी छैन। कृपया आफ्नो स्थानीय वडा कार्यालयमा सम्पर्क गर्नुहोस्। (No information available on this service. Please contact your local ward office.)", []

    results = [doc for doc, score in relevant_results]
    retrieved_text = "\n\n".join([doc.page_content for doc in results])

    prompt = f"""Answer the question using ONLY the information below. If the answer isn't in the information, say you don't know.

Information:
{retrieved_text}

Question: {question}
"""
    response = llm.invoke(prompt)
    return get_text(response), results

def get_text(response):
    if isinstance(response.content, str):
        return response.content
    # If it's a list of blocks, extract just the text parts
    return "".join(
        block["text"] for block in response.content
        if isinstance(block, dict) and block.get("type") == "text"
    )
    
print("Ready! Ask about birth registration (type 'exit' to quit)\n")

while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        break

    answer, sources = ask(question)
    print("\nAI:", answer)
    print("\n--- Sources used ---")
    for doc in sources:
        print("-", doc.page_content[:60], "...")
    print()