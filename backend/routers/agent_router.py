from fastapi import APIRouter, HTTPException, WebSocket, Depends
from typing import Dict, Optional, List
from pydantic import BaseModel
import logging
import asyncio

from agents.factory import create_agent, AgentType
from agents.base import AgentConfig
from config import get_settings
from database.prompt_store import store_prompt

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Store active WebSocket connections
active_connections: List[WebSocket] = []

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = None

class DocumentRequest(BaseModel):
    doc_id: str
    doc_type: str
    context: Optional[Dict] = None

class AgentMessage(BaseModel):
    type: str  # 'message', 'document', 'command', 'store_prompt'
    content: str
    metadata: Optional[Dict] = None

async def get_agent_config():
    settings = get_settings()
    return AgentConfig(
        model_name=settings.default_model,
        api_key=settings.openai_api_key,
        max_steps=settings.max_steps,
        planning_interval=settings.planning_interval
    )

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
async def agent_websocket(
    websocket: WebSocket,
    config: AgentConfig = Depends(get_agent_config)
):
    """WebSocket endpoint for all agent interactions"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Create a single agent instance for this connection
        agent = create_agent(AgentType.CHAT, config)
        
        while True:
            try:
                # Receive and parse message
                data = await websocket.receive_json()
                message = AgentMessage(**data)
                
                # Handle different message types
                if message.type == "document":
                    # Switch to document processing mode
                    agent = create_agent(AgentType.DOCUMENT, config)
                    context = message.metadata
                elif message.type == "store_prompt":
                    # Handle storing custom prompts
                    doc_type = message.metadata.get("doc_type")
                    if not doc_type:
                        raise ValueError("doc_type is required for storing prompts")
                        
                    success = await store_prompt(
                        doc_type=doc_type,
                        prompt=message.content
                    )
                    
                    await websocket.send_json({
                        "type": "status",
                        "content": "Prompt stored successfully" if success else "Failed to store prompt"
                    })
                    continue
                else:
                    context = message.metadata
                
                # Process through agent
                async for step in agent.process_message(message.content, context):
                    # Send step updates
                    await websocket.send_json({
                        "type": "status",
                        "content": f"Processing step {step.step_number}",
                        "metadata": {
                            "step": step.step_number,
                            "tool": step.tool_calls[0].name if step.tool_calls else None,
                            "total_steps": config.max_steps
                        }
                    })
                    
                    # If we have a final answer, send it as a message
                    if step.action_output:
                        await websocket.send_json({
                            "type": "message",
                            "content": step.action_output
                        })
                
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Processing timed out. Please try again."
                })
                
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error: {str(e)}"
                })
                
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)
            
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        if not websocket.client_state.DISCONNECTED:
            await websocket.close()

async def broadcast_to_connections(message: Dict):
    """Broadcast a message to all active connections"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logging.error(f"Error broadcasting to connection: {str(e)}")
            if connection in active_connections:
                active_connections.remove(connection) 