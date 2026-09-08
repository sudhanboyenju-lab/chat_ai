from dotenv import load_dotenv
from langchain_classic.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

print("Step 1: Loading document...")
loader = TextLoader("birth_registration.txt")
documents = loader.load()

print("Step 2: Splitting into chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.split_documents(documents)
print(f"  -> Split into {len(chunks)} chunks")

print("Step 3: Creating embeddings and storing in ChromaDB...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(chunks, embeddings)

print("Step 4: Setting up the RAG chain...")
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
    return_source_documents=True
)

print("\nReady! Ask questions about birth registration (type 'exit' to quit)\n")

while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        break

    result = qa_chain.invoke(question)
    print("AI:", result["result"])
    print("\n--- Source chunks used ---")
    for doc in result["source_documents"]:
        print(doc.page_content[:100], "...")
    print()