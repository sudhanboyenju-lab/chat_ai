import os

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from db import load_services_from_db

load_dotenv()

def setup_pipeline(embeddings):
    services = load_services_from_db()

    documents = []
    for service_id, data in services.items():
        text = f"""Service: {data['name']}
        Documents required: {', '.join(data['documents'])}
        Fee: {data['fee']}
        Office: {data['office']}
        Hours: {data['hours']}"""
        documents.append(Document(page_content=text, metadata={"source": service_id, "name": data["name"]}))

    persist_dir = "./chroma_db_json"
    if os.path.exists(persist_dir):
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    else:
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

def is_nepali(text):
    return any('\u0900' <= char <= '\u097F' for char in text)

def ask(vectorstore, llm, question, history=None, threshold=0.8):
    if history is None:
        history = []

    results_with_scores = vectorstore.similarity_search_with_score(question, k=3)
    relevant_results = [(doc, score) for doc, score in results_with_scores if score < threshold]

    if not relevant_results:
        if is_nepali(question):
            return "यो सेवाको बारेमा हामीसँग जानकारी छैन। कृपया आफ्नो स्थानीय वडा कार्यालयमा सम्पर्क गर्नुहोस्।", []
        else:
            return "We don't have information about this service. Please contact your local ward office.", []

    results = [doc for doc, score in relevant_results]
    retrieved_text = "\n\n".join([doc.page_content for doc in results])

    history_text = ""
    if history:
        history_text = "Previous conversation:\n"
        for h in history[-3:]:
            history_text += f"Citizen: {h['question']}\nAssistant: {h['answer']}\n\n"

    prompt = f"""Answer the question using ONLY the information below. Answer in the SAME language as the question (Nepali or English). 
    Pay close attention to negation words like "not", "don't", "except" - if the question asks what is NOT required, and the information only lists what IS required, clearly say you only have information on what IS required. 
    Consider the previous conversation for context. If the answer isn't in the information, say you don't know.

    {history_text}Information:
    {retrieved_text}

    Question: {question}
    """
    response = llm.invoke(prompt)
    sources = [doc.metadata.get("source", "unknown") for doc in results]
    return get_text(response), sources