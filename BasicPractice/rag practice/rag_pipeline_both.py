from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Step 1: Load multiple documents
files = ["a_birth_registration.txt", "a_map_approval.txt"]
all_documents = []
for file in files:
    loader = TextLoader(file)
    all_documents.extend(loader.load())

print(f"Loaded {len(all_documents)} documents")

# Step 2: Split
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.split_documents(all_documents)
print(f"Split into {len(chunks)} chunks")

# Step 3: Embed + store
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db_multi")

# Step 4: LLM setup
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)

def get_text(response):
    if isinstance(response.content, str):
        return response.content
    return "".join(
        block["text"] for block in response.content
        if isinstance(block, dict) and block.get("type") == "text"
    )

def ask(question):
    results = vectorstore.similarity_search(question, k=3)
    retrieved_text = "\n\n".join([doc.page_content for doc in results])

    prompt = f"""Answer the question using ONLY the information below. If the answer isn't in the information, say you don't know.

Information:
{retrieved_text}

Question: {question}
"""
    response = llm.invoke(prompt)
    return get_text(response), results

print("\nReady! Ask about birth registration or map approval (type 'exit' to quit)\n")

while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        break

    answer, sources = ask(question)
    print("\nAI:", answer)
    print("\n--- Sources used ---")
    for doc in sources:
        print(f"- [{doc.metadata.get('source', 'unknown')}]", doc.page_content[:60], "...")
    print()