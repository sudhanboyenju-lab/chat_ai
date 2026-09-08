from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

def setup_pipeline():
    files = ["a_birth_registration.txt", "a_map_approval.txt"]
    all_documents = []
    for file in files:
        loader = TextLoader(file)
        all_documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=30)
    chunks = splitter.split_documents(all_documents)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db_app")

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
    return get_text(response)