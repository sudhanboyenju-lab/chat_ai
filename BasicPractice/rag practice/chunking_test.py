from langchain_text_splitters import RecursiveCharacterTextSplitter

text = """Birth Registration Service

To register a child's birth, the following documents are required:
1. Hospital birth letter or health post certificate
2. Citizenship certificate copy of both parents
3. Marriage registration certificate (if applicable)
4. Ward recommendation letter

The service is available at the Ward Office. Registration must be completed within 35 days of birth. There is no fee for registration within this period. After 35 days, a late registration fee of Rs. 100 applies.

Office hours: Sunday to Friday, 10 AM to 5 PM."""

splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
chunks = splitter.split_text(text)

print(f"Split into {len(chunks)} chunks\n")
for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(chunk)
    print()