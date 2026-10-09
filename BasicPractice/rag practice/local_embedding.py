import torch
from transformers import AutoModel, AutoTokenizer

# Load a small, fast multilingual model (supports Nepali too)
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_local_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # Average the token embeddings to get one vector for the whole sentence
    embedding = outputs.last_hidden_state.mean(dim=1)
    return embedding[0].numpy()

text = "Birth registration requires a hospital letter."
vector = get_local_embedding(text)

print("Vector length:", len(vector))
print("First 5 numbers:", vector[:5])