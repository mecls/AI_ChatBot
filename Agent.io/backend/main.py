from fastapi import FastAPI
import ollama
import chromadb
import uuid
import requests
import os

# Initialize FastAPI app
app = FastAPI()

# Initialize ChromaDB client (in-memory for now, use persist_directory for saving)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="chat_history")



@app.get("/ask")
def ask(question: str):
    """Process a user question and provide an answer."""

# Retrieve relevant past conversations (if any exist)
    results = collection.query(query_texts=[question], n_results=50)

    # Extract previous responses (if they exist)
    past_conversations = []
    if results and "documents" in results:
        past_conversations = results["documents"]  
    else:
        past_conversations = ["No relevant past conversations found."]
        
    processed_question = f"""
    Before answering, review relevant past conversations:
    {past_conversations}

    If past conversations contain a similar question to "{question}", use them to improve your answer.

    Step-by-step reasoning:
    1. What is the user asking?
    2. What context do past conversations provide?
    3. Does the question need a different response based on past interactions?
    4. What is the most accurate and complete response?

    Respond with only the final answer, without explanations of your thought process.

    User question: {question}
    """
    # Default behavior: Ask Llama for an answer
    response = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": processed_question}])
    
    answer = response["message"]["content"]
    # Store conversation in ChromaDB
    collection.add(
        ids=[str(uuid.uuid4())],  # Unique ID (can be timestamped for better retrieval)
        documents=[f"Q: {question}\nA: {answer}"],  # Store full interaction
        metadatas=[{"question": question, "answer": answer}]  # Store metadata for easy retrieval
    )

    return {"answer": answer}

@app.get("/search")
def search(query: str):
    # Retrieve similar past conversations using ChromaDB
    results = collection.query(query_texts=[query], n_results=3)
    # Extract and return only the matched answers
    matches = results.get("documents", [])  # Extract 'documents' safely
    return {"matches": matches}
