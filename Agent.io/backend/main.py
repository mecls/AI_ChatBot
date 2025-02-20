from fastapi import FastAPI
import ollama
import chromadb
import uuid
# Initialize FastAPI app
app = FastAPI()

# Initialize ChromaDB client (in-memory for now, use persist_directory for saving)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="chat_history")

@app.get("/ask")
def ask(question: str):
    # Send user question to Ollama
    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": question}])
    answer = response["message"]["content"]

    # Store conversation in ChromaDB (indexed by user input)
    collection.add(
        ids=[str(uuid.uuid4())],  # Unique ID (can be timestamped for better retrieval)
        documents=[answer],
        metadatas=[{"question": question}]
    )

    return {"answer": answer}

@app.get("/search")
def search(query: str):
    # Retrieve similar past conversations using ChromaDB
    results = collection.query(query_texts=[query], n_results=10)
    # Extract and return only the matched answers
    matches = results.get("documents", [])  # Extract 'documents' safely
    return {"matches": matches}