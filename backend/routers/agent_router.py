from fastapi import APIRouter, HTTPException, WebSocket, Depends
from typing import Dict, Optional
from pydantic import BaseModel

from ..agents.factory import create_agent, AgentType
from ..agents.base import AgentConfig
from ..config import get_settings

router = APIRouter(prefix="/api/agent", tags=["agent"])

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None

class DocumentRequest(BaseModel):
    doc_id: str
    doc_type: str
    context: Optional[Dict] = None

@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """Handle regular chat interactions"""
    try:
        settings = get_settings()
        config = AgentConfig(
            model_name="gpt-4",
            api_key=settings.openai_api_key
        )
        
        agent = create_agent(AgentType.CHAT, config)
        response = await agent.process_message(request.message, request.context)
        
        return {
            "response": response,
            "logs": [step.dict() for step in agent.get_agent_logs()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-document")
async def analyze_document(request: DocumentRequest):
    """Handle document analysis requests"""
    try:
        settings = get_settings()
        config = AgentConfig(
            model_name="gpt-4",
            api_key=settings.openai_api_key,
            planning_interval=2  # Plan every 2 steps for document analysis
        )
        
        agent = create_agent(AgentType.DOCUMENT, config)
        response = await agent.process_message(
            f"Analyze document {request.doc_id} of type {request.doc_type}",
            context=request.context
        )
        
        return {
            "response": response,
            "logs": [step.dict() for step in agent.get_agent_logs()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Create appropriate agent based on request type
            settings = get_settings()
            config = AgentConfig(
                model_name="gpt-4",
                api_key=settings.openai_api_key
            )
            
            agent_type = AgentType.DOCUMENT if data.get("doc_id") else AgentType.CHAT
            agent = create_agent(agent_type, config)
            
            # Process message and stream updates
            async for step in agent.process_message(data["message"], data.get("context")):
                await websocket.send_json({
                    "type": "step_update",
                    "step": step.dict()
                })
                
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "detail": str(e)
        })
    finally:
        await websocket.close() 