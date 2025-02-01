from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List
from pydantic import BaseModel
import asyncio
import io
import base64
import logging
import PyPDF2
from PIL import Image
import pytesseract

# Change to relative imports
from .services.openai_service import generate_chat_response, generate_extraction_prompt
from .agents.factory import create_agent, AgentType
from .agents.base import AgentConfig
from .config import get_settings

class FileData(BaseModel):
    content: str  # Base64 encoded content
    type: str    # MIME type

class ChatMessage(BaseModel):
    content: str
    role: str
    file: Optional[FileData] = None

app = FastAPI(title="BluService", description="Backend service for BluDoc Integration Demo App")

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

@app.websocket("/chat")
async def chat_websocket(websocket: WebSocket):
    """Single WebSocket endpoint for all chat interactions"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Create agent with all available tools
        config = AgentConfig(
            model_name=settings.default_model,
            api_key=settings.openai_api_key,
            max_steps=settings.max_steps,
            planning_interval=settings.planning_interval
        )
        agent = create_agent(AgentType.CHAT, config)
        
        while True:
            try:
                # Receive message
                message = ChatMessage(**await websocket.receive_json())
                context = {}
                
                # If there's a file, process it and add to context
                if message.file:
                    file_content = message.file.content
                    file_type = message.file.type
                    
                    if not file_content:
                        raise ValueError("File content is missing")
                    
                    # Extract text from file
                    if file_type.startswith('image/'):
                        document_text = await extract_text_from_image(file_content)
                    elif file_type == 'application/pdf':
                        document_text = await extract_text_from_pdf(file_content)
                    else:
                        raise ValueError("Unsupported file format")
                        
                    # Add document info to context
                    context["document"] = {
                        "text": document_text,
                        "type": file_type
                    }
                
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
                    
                    # If we have a final answer, send it
                    if step.action_output:
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": step.action_output
                        })
                
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Processing timed out"
                })
                
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
                
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        if not websocket.client_state.DISCONNECTED:
            await websocket.close()

async def extract_text_from_pdf(content: str) -> str:
    """
    Extract text content from a PDF file
    
    Args:
        content: Base64 encoded PDF content
    """
    try:
        # Decode base64 content
        binary_content = base64.b64decode(content.split(',')[-1])  # Handle data URI format
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(binary_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

async def extract_text_from_image(content: str) -> str:
    """
    Extract text content from an image using OCR
    
    Args:
        content: Base64 encoded image content
    """
    try:
        # Handle data URI format (e.g., "data:image/jpeg;base64,/9j/4AAQSkZ...")
        if ',' in content:
            content = content.split(',', 1)[1]
            
        # Decode base64 content
        binary_content = base64.b64decode(content)
        # Open image using PIL
        image = Image.open(io.BytesIO(binary_content))
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from image: {str(e)}")

@app.post("/chat")
async def chat(message: ChatMessage):
    """Single endpoint for all chat interactions"""
    try:
        # Create agent with all available tools
        config = AgentConfig(
            model_name=settings.default_model,
            api_key=settings.openai_api_key,
            max_steps=settings.max_steps,
            planning_interval=settings.planning_interval
        )
        agent = create_agent(AgentType.CHAT, config)
        
        # Prepare context
        context = {}
        
        # If there's a file, process it and add to context
        if message.file:
            file_content = message.file.content
            file_type = message.file.type
            
            if not file_content:
                raise HTTPException(status_code=400, detail="File content is missing")
            
            # Extract text from file
            if file_type.startswith('image/'):
                document_text = await extract_text_from_image(file_content)
            elif file_type == 'application/pdf':
                document_text = await extract_text_from_pdf(file_content)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Unsupported file format. Please upload a PDF or image file."
                )
                
            # Add document info to context
            context["document"] = {
                "text": document_text,
                "type": file_type
            }
        
        # Process through agent and collect final result
        final_response = None
        steps = []
        
        async for step in agent.process_message(message.content, context):
            steps.append(step)
            if step.action_output:
                final_response = step.action_output
        
        if not final_response:
            raise HTTPException(status_code=500, detail="Agent failed to produce a response")
            
        return {
            "response": final_response,
            "steps": [
                {
                    "step_number": step.step_number,
                    "tool": step.tool_calls[0].name if step.tool_calls else None,
                    "observation": step.observations,
                    "output": step.action_output
                }
                for step in steps
            ]
        }
                
    except Exception as e:
        logging.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 