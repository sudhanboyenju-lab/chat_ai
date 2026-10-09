from dotenv import load_dotenv
from langchain_classic.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# 1. Load the document
loader = TextLoader("a_birth_registration.txt")
documents = loader.load()
# print(documents)
# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks")

# 3. Embed and store in ChromaDB
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Set up the LLM + retrieval chain
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

# 5. Ask a question
question = "What documents do I need to register a birth?"
answer = qa_chain.invoke(question)
print("\nQuestion:", question)
print("Answer:", answer["result"])