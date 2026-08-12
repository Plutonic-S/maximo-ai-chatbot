from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mangum import Mangum

from ollama_client import chat_with_tools, OLLAMA_MODEL

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Maximo AI Chatbot API",
    version="1.0.0",
    description="FastAPI orchestration backend connecting Ollama with IBM Maximo REST API tools."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    chart: Optional[Dict[str, Any]] = None
    status: str = "success"


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Maximo AI Chatbot API",
        "model": OLLAMA_MODEL
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        reply_text, chart = chat_with_tools(request.message)
        return ChatResponse(reply=reply_text, chart=chart, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")



# ASGI Handler for AWS Lambda deployment via Mangum
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
