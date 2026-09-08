from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
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

# Step 1: Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
chunks = splitter.split_text(text)
documents = [Document(page_content=chunk) for chunk in chunks]
# print(documents)
# Step 2: Embed and store in ChromaDB (this replaces your manual document_embeddings list)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(documents, embeddings)

# vectorstore = Chroma.from_documents(documents,embeddings,persist_directory="./chroma_db")

# Step 3: Search - this replaces your manual cosine_similarity + np.argmax logic
question = "What documents do I need to register a birth?"
results = vectorstore.similarity_search(question, k=2)

print("Top matching chunks:\n")
for doc in results:
    print(doc.page_content)
    print("---")
    
    
#limitaions thats why use of rag is important
