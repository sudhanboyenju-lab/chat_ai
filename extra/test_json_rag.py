from extra.json_rag_engine import ask, setup_pipeline

vectorstore, llm = setup_pipeline()

question = "What documents do I need to register a birth and is there a fee?"
answer, sources = ask(vectorstore, llm, question)
print("Answer:", answer)
print("Sources:", sources)