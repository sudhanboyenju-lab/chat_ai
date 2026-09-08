import json
import os

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

def setup_pipeline():
    with open("services_db.json", "r", encoding="utf-8") as f:
        services = json.load(f)

    documents = []
    for service_id, data in services.items():
        text = f"""Service: {data['name']}
        Documents required: {', '.join(data['documents'])}
        Fee: {data['fee']}
        Office: {data['office']}
        Hours: {data['hours']}"""
        documents.append(Document(page_content=text, metadata={"source": service_id, "name": data["name"]}))

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    persist_dir = "./chroma_db_json"
    if os.path.exists(persist_dir):
        # Database already exists - just load it, don't re-add documents
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    else:
        # First time - build it fresh
        vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=persist_dir)

    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)
    return vectorstore, llm

def get_text(response):
    if isinstance(response.content, str):
        return response.content
    return "".join(
        block["text"] for block in response.content
        if isinstance(block, dict) and block.get("type") == "text"
    )

def ask(vectorstore, llm, question, threshold=0.8):
    results_with_scores = vectorstore.similarity_search_with_score(question, k=3)
    relevant_results = [(doc, score) for doc, score in results_with_scores if score < threshold]

    if not relevant_results:
        return "यो सेवाको बारेमा हामीसँग जानकारी छैन। कृपया आफ्नो स्थानीय वडा कार्यालयमा सम्पर्क गर्नुहोस्।", []

    results = [doc for doc, score in relevant_results]
    retrieved_text = "\n\n".join([doc.page_content for doc in results])

    prompt = f"""Answer the question using ONLY the information below. If the answer isn't in the information, say you don't know.

    Information:
    {retrieved_text}

    Question: {question}
    """
    response = llm.invoke(prompt)
    sources = [doc.metadata.get("source", "unknown") for doc in results]
    return get_text(response), sources