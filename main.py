from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import our modules
from catalog_manager import CatalogManager
from agent_logic import ConversationalAgent

load_dotenv()

# Global instances
catalog_manager: Optional[CatalogManager] = None
agent: Optional[ConversationalAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    global catalog_manager, agent
    
    # Startup
    print("Loading catalog...")
    catalog_manager = CatalogManager()
    await catalog_manager.load_catalog()
    
    agent = ConversationalAgent(catalog_manager)
    print("Agent initialized")
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for SHL assessment recommendations",
    lifespan=lifespan
)


# Pydantic models for API
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint for conversational recommendations."""
    try:
        if not agent or not catalog_manager:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Get agent response
        response = await agent.process_conversation(messages)
        
        # Validate recommendations against canonical catalog records.
        validated_recs = []
        for rec in response.get("recommendations", []):
            canonical = catalog_manager.canonicalize_recommendation(rec)
            if canonical:
                validated_recs.append(Recommendation(**canonical))
        
        return ChatResponse(
            reply=response["reply"],
            recommendations=validated_recs,
            end_of_conversation=response.get("end_of_conversation", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(
            reply="I can help with SHL assessment recommendations, but I need a valid conversation message to continue.",
            recommendations=[],
            end_of_conversation=False
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
