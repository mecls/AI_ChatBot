# from fastapi import FastAPI
# import ollama
# import chromadb
# import uuid

# # Initialize FastAPI app
# app = FastAPI()

# # Initialize ChromaDB client (in-memory for now, use persist_directory for saving)
# chroma_client = chromadb.PersistentClient(path="./chroma_db")
# collection = chroma_client.get_or_create_collection(name="chat_history")



# @app.get("/ask")
# def ask(question: str):
#     """Process a user question and provide an answer."""

# # Retrieve relevant past conversations (if any exist)
#     results = collection.query(query_texts=[question], n_results=50)

#     # Extract previous responses (if they exist)
#     past_conversations = []
#     if results and "documents" in results:
#         past_conversations = results["documents"]  
#     else:
#         past_conversations = ["No relevant past conversations found."]
        
#     processed_question = f"""
#     Before answering, review relevant past conversations:
#     {past_conversations}

#     If past conversations contain a similar question to "{question}", use them to improve your answer.

#     Step-by-step reasoning:
#     1. What is the user asking?
#     2. What context do past conversations provide?
#     3. Does the question need a different response based on past interactions?
#     4. What is the most accurate and complete response?

#     Respond with only the final answer, without explanations of your thought process.

#     User question: {question}
#     """
#     # Default behavior: Ask Llama for an answer
#     response = ollama.chat(
#     model="llama3.2",
#     messages=[{"role": "user", "content": processed_question}])
    
#     answer = response["message"]["content"]
#     # Store conversation in ChromaDB
#     collection.add(
#         ids=[str(uuid.uuid4())],  # Unique ID (can be timestamped for better retrieval)
#         documents=[f"Q: {question}\nA: {answer}"],  # Store full interaction
#         metadatas=[{"question": question, "answer": answer}]  # Store metadata for easy retrieval
#     )

#     return {"answer": answer}
import datetime
from fastapi import FastAPI, Query
import ollama
import chromadb
import uuid
import os
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="chat_history")

# Connect to the LangSmith client
client = Client()

def convert_messages_to_ollama(messages):
    """Convert LangChain formatted messages to Ollama format."""
    converted_messages = []
    for message in messages:
        if hasattr(message, 'type') and hasattr(message, 'content'):
            role = 'system' if message.type == 'system' else 'user'
            converted_messages.append({
                "role": role,
                "content": message.content
            })
    return converted_messages
@app.get("/prompt")
async def ask(action: str = Query(..., title="User Question", description="Enter a question for the chatbot")):
    """Process a user question and provide an AI-generated response."""
    
    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful chatbot specialized in task management and organization."),
        ("user", "{question}")
    ])
    
    # Push prompt to LangSmith
    try:
        # Use a different prompt ID each time to avoid conflicts
        prompt_id = f"question-prompt-{uuid.uuid4().hex[:8]}"
        client.push_prompt(prompt_id, object=prompt)
        
        # Pull the prompt back from LangSmith
        retrieved_prompt = client.pull_prompt(prompt_id)
    except Exception as e:
        # Fallback to using the original prompt if LangSmith operations fail
        retrieved_prompt = prompt
        print(f"LangSmith error: {str(e)}")

    # Get past conversations
    try:
        results = collection.query(
            query_texts=[action],
            n_results=50
        )
        past_conversations = results["documents"][0] if results["documents"] else ["No relevant past conversations found."]
    except Exception as e:
        past_conversations = [f"Error retrieving past conversations: {str(e)}"]

    # Process the question with context
    processed_question = f"""
    Past conversations for context: {past_conversations}

    Current question: {action}

    Please provide a direct and relevant response based on both the current question and any applicable past context.
    """

    # Format the prompt using the retrieved prompt template
    formatted_messages = retrieved_prompt.format_messages(question=processed_question)
    
    # Convert messages to Ollama format
    ollama_messages = convert_messages_to_ollama(formatted_messages)

    # Generate response using Ollama
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=ollama_messages
        )
        answer = response["message"]["content"]
    except Exception as e:
        return {"error": f"Error generating response: {str(e)}"}

    # Store conversation in ChromaDB
    try:
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[f"Q: {action}\nA: {answer}"],
            metadatas=[{
                "question": action,
                "answer": answer,
                "timestamp": datetime.datetime.now().isoformat()
            }]
        )
    except Exception as e:
        return {"error": f"Failed to store conversation: {str(e)}", "answer": answer}

    return {"answer": answer}

@app.get("/search")
def search(query: str):
    # Retrieve similar past conversations using ChromaDB
    results = collection.query(query_texts=[query], n_results=3)
    # Extract and return only the matched answers
    matches = results.get("documents", [])  # Extract 'documents' safely
    return {"matches": matches}

