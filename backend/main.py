from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Union
from pydantic import BaseModel, field_validator
import asyncio
import io
import base64
import logging
import PyPDF2
from PIL import Image
import pytesseract
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import sys

# Change to relative imports
from .services.openai_service import generate_chat_response, generate_extraction_prompt
from .agents.openai_agent import OpenAIAgent
from .config import get_settings

class FileData(BaseModel):
    content: Union[str, List[int]]  # Can be either base64 string or byte array
    type: str    # MIME type
    
    @field_validator('content')
    def validate_content(cls, v):
        if isinstance(v, list):
            # Convert byte array to base64 string
            return base64.b64encode(bytes(v)).decode('utf-8')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "base64_encoded_string",
                "type": "application/pdf"
            }
        }
    }

class ChatMessage(BaseModel):
    content: str
    role: str = "user"  # Default to "user"
    file: Optional[FileData] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Please analyze this document",
                "role": "user",
                "file": {
                    "content": "base64_encoded_string",
                    "type": "application/pdf"
                }
            }
        }
    }

app = FastAPI(title="BluService", description="Backend service for BluDoc Integration Demo App")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with more detail"""
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"Request validation error: {exc_str}")
    # Log the actual request body
    body = await request.body()
    logging.error(f"Request body: {body.decode()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc_str},
    )

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
        agent = OpenAIAgent(
            model_name=settings.default_model,
            api_key=settings.openai_api_key,
            system_prompt="You are a helpful assistant."
        )
        
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
async def chat(request: Request, message: ChatMessage):
    """Endpoint for chat interactions using OpenAI's API with function calling."""
    try:
        # Log the raw request for debugging
        body = await request.body()
        logging.info(f"Raw request body: {body.decode()}")
        logging.info(f"Parsed message: {message.dict()}")
        
        # Log incoming request
        logging.info(f"Received chat request with content: {message.content}")
        if message.file:
            logging.info(f"File included of type: {message.file.type}")
        
        # Prepare context (if a file is provided)
        context: Dict = {}
        if message.file:
            file_content = message.file.content
            file_type = message.file.type
            
            if not file_content:
                raise HTTPException(status_code=400, detail="File content is missing")
            
            logging.info(f"Processing file of type: {file_type}")
            
            try:
                if file_type.startswith('image/'):
                    document_text = await extract_text_from_image(file_content)
                elif file_type == 'application/pdf':
                    document_text = await extract_text_from_pdf(file_content)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Unsupported file format. Please upload a PDF or image file."
                    )
                    
                logging.info("Successfully extracted text from document")
                
                context["document"] = {
                    "text": document_text,
                    "type": file_type
                }
            except Exception as e:
                logging.error(f"Error processing file: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
        
        # Create the new agent instance (using OpenAIAgent).
        agent = OpenAIAgent(
            model_name=settings.default_model,
            api_key=settings.openai_api_key,
            system_prompt="You are a helpful assistant."
        )
        
        final_response = await agent.process_message(message.content, context)
        
        return {
            "response": final_response
        }
                
    except Exception as e:
        logging.error(f"Error processing chat: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 