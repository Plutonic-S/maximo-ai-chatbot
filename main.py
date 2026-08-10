import os
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from mangum import Mangum
from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError

from maximo_mcp_server import fetch_service_requests, fetch_locations, fetch_classifications

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing from environment variables.")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Define list of tools available via MCP/Python wrappers
MAXIMO_TOOLS = [fetch_service_requests, fetch_locations, fetch_classifications]

app = FastAPI(
    title="Maximo AI Chatbot API",
    version="1.0.0",
    description="FastAPI orchestration backend connecting Gemini AI with IBM Maximo REST API tools."
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
    status: str = "success"


def generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Helper to handle Gemini content generation with backoff on 429 rate limits."""
    delay = 5
    system_instruction = (
        "You are a helpful IBM Maximo AI Assistant. "
        "When asked to count or calculate the total number of service requests/tickets, locations, or classifications, "
        "always call the corresponding tool (e.g., fetch_service_requests, fetch_locations, or fetch_classifications) with count_only=True. "
        "This uses the native Maximo ?count=1 OSLC parameter to instantly return the exact total count. "
        "When presenting tabular data (such as service requests, tickets, locations, or classifications), "
        "ALWAYS format them as standard GitHub-Flavored Markdown (GFM) tables with explicit newlines between every row and header. "
        "Each table row must be on its own line separated by a newline character. "
        "Example format:\n"
        "| Ticket ID | Location | Status | Description | Reported By | Date Reported |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        "| 1187 | 764750 | NEW | Keyboard issue | MAXADMIN | 2025-03-02 |\n"
    )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=MAXIMO_TOOLS,
                    temperature=0.2
                )
            )
            return response.text or "I processed your request, but received no text response."
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    print(f"Rate limit reached (429). Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e
        except Exception as e:
            raise e
    raise HTTPException(status_code=429, detail="Gemini API rate limit exceeded. Please retry in a few moments.")


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Maximo AI Chatbot API",
        "model": MODEL_NAME
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    try:
        reply_text = generate_with_retry(request.message)
        return ChatResponse(reply=reply_text, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# ASGI Handler for AWS Lambda deployment via Mangum
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
